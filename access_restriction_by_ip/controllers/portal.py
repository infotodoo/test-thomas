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
from odoo.addons.portal.controllers.web import Home
from odoo.http import request
from odoo.exceptions import Warning
import odoo
import odoo.modules.registry
from odoo.tools.translate import _
from odoo import http


class Home_inherit(Home):

    @http.route()
    def index(self, *args, **kw):
        ip_address = request.httprequest.environ['REMOTE_ADDR']
        ip_list = []
        for ip in request.env['allowed.ips'].sudo().search([]):
            ip_list.append(ip.ip_address)

        if not ip_address in ip_list:
            return 'IP DO NOT ALLOWED'
        else:
            if request.session.uid and not request.env['res.users'].sudo().browse(request.session.uid).has_group('base.group_user'):
                return http.local_redirect('/my', query=request.params, keep_hash=True)
            return super(Home, self).index(*args, **kw)

    def _login_redirect(self, uid, redirect=None):
        if not redirect and not request.env['res.users'].sudo().browse(uid).has_group('base.group_user'):
            return '/web/login'
        return super(Home, self)._login_redirect(uid, redirect=redirect)