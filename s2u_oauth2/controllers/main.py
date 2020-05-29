# -*- coding: utf-8 -*-

# Odoo imports
from odoo.addons.auth_oauth.controllers.main import OAuthLogin
from odoo.addons.web.controllers.main import db_monodb, ensure_db, set_cookie_and_redirect, login_and_redirect
import logging
import werkzeug.urls
import werkzeug.utils
import requests
from odoo import http, _
from odoo.http import request

# External imports
import json
import uuid
import random
from passlib.context import CryptContext

_logger = logging.getLogger(__name__)

#############################
# Authentication Controller #
#############################


class MSLogin(OAuthLogin):

    # Function overwriten for OAuthLogin
    def list_providers(self):
        try:
            providers = request.env['auth.oauth.provider'].sudo().search_read([
                ('enabled', '=', True),
                ('secret_key', '!=', ''),
            ])
        except Exception:
            providers = []

        for provider in providers:
            msuuid = uuid.uuid4()
            request.session['msauth.msuuid'] = '%s|%d' % (msuuid, provider['id'])
            request.session['msauth.session_db'] = request.session.db
            scope = provider['scope']
            params = dict(
                scope=scope,
                response_type='code',
                client_id=provider['client_id'],
                redirect_uri=request.httprequest.url_root + 'auth_oauth/microsoft',
                state=request.session['msauth.msuuid']
            )
            provider['auth_link'] = "%s?%s" % (provider['auth_endpoint'], werkzeug.url_encode(params))
        return providers

    @http.route('/auth_oauth/microsoft', type='http', auth='public', website=True)
    def signin(self, **kw):
        if not request.session['msauth.msuuid']:
            return werkzeug.utils.redirect('/web/login?err=Auth session expired - Try again', code=302)
        if request.params.get('state').replace('%7', '|') != request.session['msauth.msuuid']:
            request.session['msauth.msuuid'] = None
            return request.render('http_routing.http_error',
                                  {'status_code': _('Bad Request'),
                                   'status_message': _('State check failed (1). Try again.')})

        provider_id = request.session['msauth.msuuid'].split('|')[1]

        if not request.params.get('code'):
            return request.render('http_routing.http_error',
                                  {'status_code': _('Bad Request'),
                                   'status_message': _(
                                   'Expected "code" param in URL, but its not there. Try again. Or contact Administrator'
                                   )
                                  })

        request.session['msauth.msuuid'] = None
        code = request.params.get('code')
        profile = self._validate(code, provider_id)

        if not profile:
            return request.render('http_routing.http_error',
                                  {'status_code': _('Bad Request'),
                                   'status_message': _('Profile validation failed. Try again. Or contact Administrator')})

        # sure the user is authentic, but do they have a login for this DB? --> If user not exist in DB --> user is not allowed
        if 'userPrincipalName' not in profile:
            return request.render('http_routing.http_error',
                                  {'status_code': _('msauth'),
                                   'status_message': _('Your profile does not have an email')})
        login = profile['userPrincipalName']
        # Generate temp password so user can login
        password = self._ensure_password(login)

        if not password:
            _logger.error("User %s tried to login but failed " % profile['userPrincipalName'])
            return request.render('http_routing.http_error',
                                  {'status_code': _('Bad Request'),
                                   'status_message': _('You (%s) are not allowed access to this database (1)' % profile['userPrincipalName'] )})
        login_uid = request.session.authenticate(request.session['msauth.session_db'], login, password)
        if login_uid is False:
            return request.render('http_routing.http_error',
                                  {'status_code': _('Bad Request'),
                                   'status_message': _('You are not allowed access to this database (2)')})

        return set_cookie_and_redirect('/web')

    @http.route('/web/session/logout', type='http', auth="user")
    def logout(self, redirect='/web'):
        if 'msauth.id_token' in request.session:
            request.session.logout(keep_db=True)
            return http.local_redirect(
                "https://login.microsoftonline.com/common/oauth2/v2.0/logout?post_logout_redirect_uri=" +
                request.httprequest.url_root + "/web"
            )
        else:
            request.session.logout(keep_db=True)
        return werkzeug.utils.redirect(redirect, 303)

    def _validate(self, authorization_code, provider_id):
        # lookup the secret for the provider
        provider = request.env['auth.oauth.provider'].sudo().search_read([('id', '=', provider_id)])
        if not len(provider):
            return False
        provider = provider[0]
        # config may have changed during login process so we make sure we still have values we need
        if not provider['client_id'] or not provider['secret_key'] or not provider['validation_endpoint']:
            return False
        # exchange the authorization code for an access token
        post_data = {
            "grant_type": 'authorization_code',
            "code": authorization_code,
            "client_id": provider['client_id'],
            "client_secret": provider['secret_key'],
            "redirect_uri": request.httprequest.url_root + 'auth_oauth/microsoft'
        }
        try:
            access_token_response = requests.post(provider['validation_endpoint'], data=post_data, verify=False)
        except Exception as e:
            _logger.error('%s API request failed: status code=%s; reason=%s'
                          % (provider['validation_endpoint'], e.code, e.reason))
            return False
        try:
            data = json.loads(access_token_response.content)
        except Exception as e:
            _logger.error('failed decoding JSON response from %s: %s'
                          % (provider['validation_endpoint'], json.dumps(e)))
            return False

        if 'access_token' not in data:
            _logger.error('MSAuth expected id_token to be returned from %s' % provider['validation_endpoint'])
            return False
        request.session['msauth.id_token'] = data['access_token']
        request.session['msauth.provider_id'] = provider_id

        graph_data = requests.get(
            'https://graph.microsoft.com/v1.0/me',
            headers={'Authorization': 'Bearer ' + data['access_token']})
        data = json.loads(graph_data.content)
        if 'error' in data:
            return False
        return data

    def _ensure_password(self, login):
        # get the id as variant value for the encrypted password
        # this way we also ensure the user's login even exists
        login = request.env['res.users'].sudo().search_read([('login', '=', login)])
        if not len(login):
            param = request.env['ir.config_parameter'].sudo().search(
                [('key', '=', 's2u_msaccount')], limit=1)
            if not param or param.value.lower() != 'true':
                return False
            else:
                # Creating user (no password yet)
                user_vals = {
                    'name': user,
                    'login': user
                }
                login = request.env['res.users'].sudo().create(user_vals)
        login = login[0]
        # generate a temporary hashed password and set it in the database
        tmp_password = '%032x' % random.getrandbits(128)
        # paradigm from odoo.addons.auth_crypt.models.res_users
        encrypted = CryptContext(['pbkdf2_sha512']).encrypt(tmp_password)
        request.env.cr.execute(
            "UPDATE res_users SET password=%s WHERE id=%s",
            (encrypted, login['id']))
        request.env.cr.commit()
        # we can now login with this temporary password
        return tmp_password
