# -*- coding: utf-8 -*-
from odoo import http, models
import odoo.addons.web.controllers.main as main


class DataSetController(main.DataSet):

    @http.route(['/web/dataset/call_kw', '/web/dataset/call_kw/<path:path>'], type='json', auth="user")
    def call_kw(self, model, method, args, kwargs, path=None):
        models._logger.error('lalalala')
        return super(DataSetController, self).call_kw(model, method, args, kwargs)

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