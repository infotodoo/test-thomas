# -*- coding: utf-8 -*-
# from odoo import http


# class AccessThomas(http.Controller):
#     @http.route('/access_thomas/access_thomas/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/access_thomas/access_thomas/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('access_thomas.listing', {
#             'root': '/access_thomas/access_thomas',
#             'objects': http.request.env['access_thomas.access_thomas'].search([]),
#         })

#     @http.route('/access_thomas/access_thomas/objects/<model("access_thomas.access_thomas"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('access_thomas.object', {
#             'object': obj
#         })
