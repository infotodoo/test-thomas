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
from odoo.addons.web.controllers import main
from odoo.http import request
from odoo.exceptions import Warning
import odoo
import odoo.modules.registry
from odoo.tools.translate import _
from odoo import http
import logging

_logger = logging.getLogger(__name__)

class Home(main.Home):

    @http.route('/web/login', type='http', auth="public")
    def web_login(self, redirect=None, **kw):
        main.ensure_db()
        company = request.env['res.company']._get_main_company()
        block = company.block_ips
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            if block:
                ip_address = request.httprequest.environ['REMOTE_ADDR']
                ip_list = []

                for ip in request.env['allowed.ips'].sudo().search([]):
                    ip_list.append(ip.ip_address)

                if not ip_address in ip_list or not block:
                    return ('<html><br /><br /><br /><br /><h1 style=\
                            "text-align: center;">{}<br /><br />IP DO NOT ALLOWED</h1></html>\
                                '.format(ip_address))
                else:
                    return http.redirect_with_hash(redirect)
            else:
                return http.redirect_with_hash(redirect)

        if not request.uid:
            request.uid = odoo.SUPERUSER_ID

        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        ip_address = request.httprequest.environ['REMOTE_ADDR']
        ip_list = []

        for ip in request.env['allowed.ips'].sudo().search([]):
            ip_list.append(ip.ip_address)

        if not ip_address in ip_list or not block:
            return ('<html><br /><br /><br /><br /><h1 style=\
                    "text-align: center;">{}<br /><br />IP DO NOT ALLOWED</h1></html>\
                        '.format(ip_address))
        else:
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