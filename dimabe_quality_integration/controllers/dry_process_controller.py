from odoo import http, exceptions, models
from odoo.http import request
import werkzeug

class DryProcessController(http.Controller):
    
    @http.route('/api/dry_process', type='json', methods=['GET'], auth='token', cors='*')
    def get_dry_process(self):
        res = request.env['dried.unpelled.history'].sudo().search([])
        return {
            'data': res
        }