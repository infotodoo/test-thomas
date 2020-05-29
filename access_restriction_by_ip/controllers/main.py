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


class Home(main.Home):

    @http.route('/web/login', type='http', auth="public")
    def web_login(self, redirect=None, **kw):
        main.ensure_db()
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
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

        if not ip_address in ip_list:
            #values['error'] = _("Not allowed to login from this IP")
            return 'IP DO NOT ALLOWED'#request.render('web.login', values)
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

    @http.route()
    def index(self, *args, **kw):
        ip_address = request.httprequest.environ['REMOTE_ADDR']
        ip_list = []
        for ip in request.env['allowed.ips'].sudo().search([]):
            ip_list.append(ip.ip_address)

        if not ip_address in ip_list:
            return 'IP DO NOT ALLOWED'

        # if request.session.uid and not request.env['res.users'].sudo().browse(request.session.uid).has_group('base.group_user'):
        #     return http.local_redirect('/my', query=request.params, keep_hash=True)
        # return super(Home, self).index(*args, **kw)