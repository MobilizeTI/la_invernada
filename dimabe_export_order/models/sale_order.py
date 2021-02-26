from odoo import fields, models,api
import json
from odoo.tools import date_utils

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_number = fields.Char('Contrato')

    ship_ids = fields.Many2many('custom.ship', compute="compute_ships")

    def compute_ships(self):
        for item in self:
            item.ship_ids = item.picking_ids.mapped('ship') 
