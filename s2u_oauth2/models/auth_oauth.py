# -*- coding: utf-8 -*-

from odoo import fields, models


class AuthOAuthProvider(models.Model):

    _inherit = 'auth.oauth.provider'
    _description = 'S2U OAuth2 provider'
    _order = 'name'

    # Add secret_key for Microsoft
    secret_key = fields.Char(string='Secret Key')
