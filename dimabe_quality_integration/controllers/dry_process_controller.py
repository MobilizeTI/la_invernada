from odoo import http, exceptions, models
from odoo.http import request
import werkzeug

class DryProcessController(http.Controller):
    
    @http.route('/api/dry_process', type='json', methods=['GET'], auth='token', cors='*')
    def get_dry_process(self):
        res = request.env['dried.unpelled.history'].sudo().search([])
        return res.read([
            'name',
            'in_lot_ids',
            'init_date',
            'lot_guide_numbers',
            'finish_date',
            'in_product_id.name',
            'in_product_variety',
            'out_lot_id.name'
        ])