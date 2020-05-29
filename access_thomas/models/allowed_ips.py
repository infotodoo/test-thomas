# -*- coding: utf-8 -*-

from odoo import models, fields

class AllowedIPs(models.Model):
    _name = 'allowed.ips'

    ip_address = fields.Char(string='Allowed IP')
    name = fields.Char('Name')