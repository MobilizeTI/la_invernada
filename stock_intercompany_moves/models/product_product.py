# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, exceptions, SUPERUSER_ID
import logging
_logger = logging.getLogger('TEST =====')


class Product(models.Model):
    _inherit = 'product.product'

    def action_open_quants(self):
        action = super(Product, self).action_open_quants()
        action.update({
            'domain': [('product_id', 'in', self.ids), ('company_id', '!=', False)]
        })
        action['context'].update({
            'allowed_company_ids': []
        })
        return action