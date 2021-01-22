from odoo import fields, models,api
import json
from odoo.tools import date_utils

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_number = fields.Char('Contrato')

    @api.multi
    def get_invoice_ids(self):
        for item in self.invoice_ids:
            raw_data = item.read()
            json_data = json.dumps(raw_data,default=date_utils.json_default)
            json_dict = json.loads(json_data)
            models._logger.error(json_dict)
