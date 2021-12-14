# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, exceptions, SUPERUSER_ID


class StockLocation(models.Model):
    _inherit = 'stock.location'
    
    is_inter_company = fields.Boolean('¿Es una ubicación inter-compañía?')
    
    @api.onchange('is_inter_company')
    def _onchange_is_inter_company(self):
        if self.is_inter_company:
            self.company_id = False