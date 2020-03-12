# -*- coding: utf-8 -*-
from odoo import http
import odoo.addons.web.controllers.main as main
import logging

_logger = logging.getLogger(__name__)


class DataSetController(main.DataSet):

    @http.route(['/web/dataset/call_kw', '/web/dataset/call_kw/<path:path>'], type='json', auth="user")
    def call_kw(self, model, method, args, kwargs, path=None):
        res = super(DataSetController, self).call_kw(model, method, args, kwargs)
        if model == 'stock.production.lot' and method == 'onchange':
            for reg in args:
                if 'id' in reg:
                    lot_id = http.request.env['stock.production.lot'].search([('id', '=', reg['id'])])
                    if lot_id:
                        if 'stock_production_lot_serial_ids' in reg:
                            lot_id.write({
                                'stock_production_lot_serial_ids': reg['stock_production_lot_serial_ids']
                            })
            _logger.error(res)
            _logger.error(args)

        return res

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