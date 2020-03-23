from odoo import http, exceptions, models
from odoo.http import request
import werkzeug

class DryProcessController(http.Controller):
    
    @http.route('/api/dry_process', type='json', methods=['GET'], auth='token', cors='*')
    def get_dry_process(self):
        result = request.env['dried.unpelled.history'].sudo().search([])
        processResult = []
        for res in result: 
            processResult.append({
                'name': res.name,
                'in_lot_ids': res.mapped('in_lot_ids.name'),
                'init_date': res.init_date,
                'lot_guide_numbers': res.lot_guide_numbers,
                'finish_date': res.finish_date,
                'in_product_id': res.in_product_id.name,
                'in_product_variety': res.in_product_variety,
                'out_lot_id': res.out_lot_id.name,
                'producer_id': res.producer_id.name,
                'total_in_weight': res.total_in_weight,
                'total_out_weight': res.total_out_weight,
                'perfomance': res.performance
            })
        return processResult