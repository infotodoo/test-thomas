# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    block_ips = fields.Boolean('Block connection by IP', default=False, help="\
        The Block field allows you to block your site from unknow connection.")
