# -*- coding: utf-8 -*-
from odoo import http

# class DimabeManufacturing(http.Controller):
#     @http.route('/dimabe_manufacturing/dimabe_manufacturing/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dimabe_manufacturing/dimabe_manufacturing/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dimabe_manufacturing.listing', {
#             'root': '/dimabe_manufacturing/dimabe_manufacturing',
#             'objects': http.request.env['dimabe_manufacturing.dimabe_manufacturing'].search([]),
#         })

#     @http.route('/dimabe_manufacturing/dimabe_manufacturing/objects/<model("dimabe_manufacturing.dimabe_manufacturing"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dimabe_manufacturing.object', {
#             'object': obj
#         })
