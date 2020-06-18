# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Niyas Raphy(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import base64
import datetime
import json
import os
import logging
import pytz
import requests
import werkzeug.utils
import werkzeug.wrappers

from itertools import islice
from xml.etree import ElementTree as ET

import odoo
import odoo.modules.registry

from odoo import http
from odoo.http import request
from odoo.tools.translate import _
from odoo.exceptions import Warning
from odoo.addons.web.controllers import main

_logger = logging.getLogger(__name__)

class Home(main.Home):

    def _block_ips(self):
        company = request.env['res.company']._get_main_company()
        block = company.block_ips
        if block:
            ip_address = request.httprequest.environ['REMOTE_ADDR']
            ip_list = []

            for ip in request.env['allowed.ips'].sudo().search([]):
                ip_list.append(ip.ip_address)

            if not ip_address in ip_list and block:
                return ('<html><br /><br /><br /><br /><h1 style=\
                        "text-align: center;">{}<br /><br />IP DO NOT ALLOWED</h1></html>\
                            '.format(ip_address))
            else:
                return False
        else:
            return block

    @http.route('/web/login', type='http', auth="public")
    def web_login(self, redirect=None, **kw):
        main.ensure_db()
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            block = self._block_ips()
            if block:
                return block
            #     ip_address = request.httprequest.environ['REMOTE_ADDR']
            #     ip_list = []

            #     for ip in request.env['allowed.ips'].sudo().search([]):
            #         ip_list.append(ip.ip_address)

            #     if not ip_address in ip_list and block:
            #         return ('<html><br /><br /><br /><br /><h1 style=\
            #                 "text-align: center;">{}<br /><br />IP DO NOT ALLOWED</h1></html>\
            #                     '.format(ip_address))
            #     else:
            #         return http.redirect_with_hash(redirect)
            # else:
            return http.redirect_with_hash(redirect)

        if not request.uid:
            request.uid = odoo.SUPERUSER_ID

        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None
        
        block = self._block_ips()
        if block:
            return block
        # ip_address = request.httprequest.environ['REMOTE_ADDR']
        # ip_list = []

        # for ip in request.env['allowed.ips'].sudo().search([]):
        #     ip_list.append(ip.ip_address)

        # if not ip_address in ip_list and block:
        #     return ('<html><br /><br /><br /><br /><h1 style=\
        #             "text-align: center;">{}<br /><br />IP DO NOT ALLOWED</h1></html>\
        #                 '.format(ip_address))
        if request.httprequest.method == 'POST':
            old_uid = request.uid
            if request.params['login']:
                try:
                    uid = request.session.authenticate(request.session.db,
                                                    request.params[
                                                        'login'],
                                                    request.params[
                                                        'password'])
                    request.params['login_success'] = True
                    return http.redirect_with_hash(
                        self._login_redirect(uid, redirect=redirect))
                except odoo.exceptions.AccessDenied as e:
                    request.uid = old_uid
                    if e.args == odoo.exceptions.AccessDenied().args:
                        values['error'] = _("Wrong login/password")

        return request.render('web.login', values)

    @http.route(['/robots.txt'], type='http', auth="user")
    def robots(self, **kwargs):
        block = self._block_ips()
        if block:
            return block
        return request.render('website.robots', {'url_root': request.httprequest.url_root}, mimetype='text/plain')

    @http.route('/sitemap.xml', type='http', auth="user", website=True, multilang=False, sitemap=False)
    def sitemap_xml_index(self, **kwargs):
        current_website = request.website
        Attachment = request.env['ir.attachment'].sudo()
        View = request.env['ir.ui.view'].sudo()
        mimetype = 'application/xml;charset=utf-8'
        content = None
        block = self._block_ips()
        if block:
            return block

        def create_sitemap(url, content):
            return Attachment.create({
                'datas': base64.b64encode(content),
                'mimetype': mimetype,
                'type': 'binary',
                'name': url,
                'url': url,
            })
        dom = [('url', '=', '/sitemap-%d.xml' % current_website.id), ('type', '=', 'binary')]
        sitemap = Attachment.search(dom, limit=1)
        if sitemap:
            # Check if stored version is still valid
            create_date = fields.Datetime.from_string(sitemap.create_date)
            delta = datetime.datetime.now() - create_date
            if delta < SITEMAP_CACHE_TIME:
                content = base64.b64decode(sitemap.datas)

        if not content:
            # Remove all sitemaps in ir.attachments as we're going to regenerated them
            dom = [('type', '=', 'binary'), '|', ('url', '=like', '/sitemap-%d-%%.xml' % current_website.id),
                   ('url', '=', '/sitemap-%d.xml' % current_website.id)]
            sitemaps = Attachment.search(dom)
            sitemaps.unlink()

            pages = 0
            locs = request.website.with_user(request.website.user_id).enumerate_pages()
            while True:
                values = {
                    'locs': islice(locs, 0, LOC_PER_SITEMAP),
                    'url_root': request.httprequest.url_root[:-1],
                }
                urls = View.render_template('website.sitemap_locs', values)
                if urls.strip():
                    content = View.render_template('website.sitemap_xml', {'content': urls})
                    pages += 1
                    last_sitemap = create_sitemap('/sitemap-%d-%d.xml' % (current_website.id, pages), content)
                else:
                    break

            if not pages:
                return request.not_found()
            elif pages == 1:
                # rename the -id-page.xml => -id.xml
                last_sitemap.write({
                    'url': "/sitemap-%d.xml" % current_website.id,
                    'name': "/sitemap-%d.xml" % current_website.id,
                })
            else:
                # TODO: in master/saas-15, move current_website_id in template directly
                pages_with_website = ["%d-%d" % (current_website.id, p) for p in range(1, pages + 1)]

                # Sitemaps must be split in several smaller files with a sitemap index
                content = View.render_template('website.sitemap_index_xml', {
                    'pages': pages_with_website,
                    'url_root': request.httprequest.url_root,
                })
                create_sitemap('/sitemap-%d.xml' % current_website.id, content)
        return request.make_response(content, [('Content-Type', mimetype)])

    @http.route('/website/info', type='http', auth="user", website=True)
    def website_info(self, **kwargs):
        block = self._block_ips()
        if block:
            return block
        try:
            request.website.get_template('website.website_info').name
        except Exception as e:
            return request.env['ir.http']._handle_exception(e, 404)
        Module = request.env['ir.module.module'].sudo()
        apps = Module.search([('state', '=', 'installed'), ('application', '=', True)])
        l10n = Module.search([('state', '=', 'installed'), ('name', '=like', 'l10n_%')])
        values = {
            'apps': apps,
            'l10n': l10n,
            'version': odoo.service.common.exp_version()
        }
        return request.render('website.website_info', values)
class Session(main.Session):
    
    @http.route('/web/session/authenticate', type='json', auth="none")
    def authenticate(self, db, login, password, base_location=None):
        ip_address = request.httprequest.environ['REMOTE_ADDR']
        ip_list = []
        company = request.env['res.company']._get_main_company()
        block = company.block_ips

        for ip in request.env['allowed.ips'].sudo().search([]):
            ip_list.append(ip.ip_address)
        
        if not ip_address in ip_list and block:
            return 'IP DO NOT ALLOWED {}'.format(ip_address)
        else:
            request.session.authenticate(db, login, password)
            return request.env['ir.http'].session_info()
