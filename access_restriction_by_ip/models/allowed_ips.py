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
from odoo import models, fields, http
from odoo.http import request


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    def block_ips(self):
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

    @classmethod
    def _dispatch(cls):
        # add signup token or login to the session if given
        block = request.env['ir.http'].block_ips()
        if block:
            return block
        return super(Http, cls)._dispatch()


class AllowedIPs(models.Model):
    _name = 'allowed.ips'
    _description = 'Allowes IPS'

    ip_address = fields.Char(string='Allowed IP')
    name = fields.Char('Name')