from odoo import fields, models,api
import json
from odoo.tools import date_utils

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_number = fields.Char('Contrato')

    ship_ids = fields.Many2many('custom.ship', string="Nave",compute="compute_ships")

    ordered_quantity = fields.Float(string="Cantidad Pedida", compute="compute_ordered_quantity")

    delivered_quantity = fields.Float(string="Cantidad Entregada", compute="compute_delivered_quantity")

    def compute_ships(self):
        for item in self:
            item.ship_ids = item.picking_ids.mapped('ship') 
    
    def compute_ordered_quantity(self):
        for item in self:
            item.ordered_quantity = item.order_line[0].product_uom_qty

    def compute_delivered_quantity(self):
        for item in self:
            item.ordered_quantity = item.order_line[0].qty_delivered

