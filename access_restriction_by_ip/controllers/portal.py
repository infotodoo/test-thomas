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
from odoo.addons.website.controllers.main import Website
from odoo.http import request
from odoo.exceptions import Warning
import odoo
import odoo.modules.registry
from odoo.tools.translate import _
from odoo import http
from werkzeug.utils import redirect


class  Website( Website):

    @http.route('/', type='http', auth="public", website=True)
    def index(self, **kw):
        ip_address = request.httprequest.environ['REMOTE_ADDR']
        ip_list = []
        for ip in request.env['allowed.ips'].sudo().search([]):
            ip_list.append(ip.ip_address)

        if not ip_address in ip_list:
            return ('<html><br /><br /><br /><h1 style="text-align: center;">IP DO NOT ALLOWED</h1></html>')

        else:
            homepage = request.website.homepage_id
            if homepage and (homepage.sudo().is_visible or request.env.user.has_group('base.group_user')) and homepage.url != '/':
                return request.env['ir.http'].reroute(homepage.url)

            website_page = request.env['ir.http']._serve_page()
            if website_page:
                return website_page
            else:
                top_menu = request.website.menu_id
                first_menu = top_menu and top_menu.child_id and top_menu.child_id.filtered(lambda menu: menu.is_visible)
                if first_menu and first_menu[0].url not in ('/', '', '#') and (not (first_menu[0].url.startswith(('/?', '/#', ' ')))):
                    return request.redirect(first_menu[0].url)

            raise request.not_found()

    @http.route(website=True, auth="public", sitemap=False)
    def web_login(self, redirect=None, *args, **kw):
        ip_address = request.httprequest.environ['REMOTE_ADDR']
        ip_list = []
        for ip in request.env['allowed.ips'].sudo().search([]):
            ip_list.append(ip.ip_address)

        if not ip_address in ip_list:
            return ('<html><br /><br /><br /><h1 style="text-align: center;">IP DO NOT ALLOWED</h1></html>')

        else:
            response = super(Website, self).web_login(redirect=redirect, *args, **kw)
            if not redirect and request.params['login_success']:
                if request.env['res.users'].browse(request.uid).has_group('base.group_user'):
                    redirect = b'/web?' + request.httprequest.query_string
                else:
                    redirect = '/my'
                return http.redirect_with_hash(redirect)
            return response
