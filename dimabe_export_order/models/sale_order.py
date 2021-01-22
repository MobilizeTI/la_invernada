from odoo import fields, models,api
import json
from odoo.tools import date_utils

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_number = fields.Char('Contrato')

