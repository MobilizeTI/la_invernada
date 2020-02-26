from odoo import fields, models,api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_number = fields.Char('Contrato')
