from odoo import http, exceptions, models
from odoo.http import request
from datetime import date, timedelta
import werkzeug

class DryProcessController(http.Controller):
    
    @http.route('/api/dry_process', type='json', methods=['GET'], auth='token', cors='*')
    def get_dry_process(self, sinceDate = None):
        search_date = sinceDate or (date.today() - timedelta(days=1))
        result = request.env['dried.unpelled.history'].sudo().search([('write_date', '>=', search_date)])
        processResult = []
        for res in result: 
            processResult.append({
                'name': res.name,
                'inLotIds': res.mapped('in_lot_ids.name'),
                'initDate': res.init_date,
                'guideNumbers': res.lot_guide_numbers,
                'finishDate': res.finish_date,
                'productName': res.in_product_id.name,
                'productId': res.in_product_id.id,
                'productVariety': res.in_product_variety,
                'outLot': res.out_lot_id.name,
                'producerName': res.producer_id.name,
                'producerId': res.producer_id.id,
                'totalInWeight': res.total_in_weight,
                'totalOutWeight': res.total_out_weight,
                'performance': res.performance,
                'OdooUpdatedAt': res.write_date
            })
        return processResult