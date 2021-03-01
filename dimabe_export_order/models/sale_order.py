from odoo import fields, models,api
import json
from odoo.tools import date_utils

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_number = fields.Char('Contrato')

    ship_ids = fields.Many2many('custom.ship', string="Nave",compute="compute_ships")

    ordered_quantity = fields.Float(string="Cantidad Pedida", compute="compute_ordered_quantity")

    delivered_quantity = fields.Float(string="Cantidad Entregada", compute="compute_delivered_quantity")

    unit_price = fields.Float(string="Precio Unitario", compute="compute_unit_price")

    departure_date = fields.Datetime(string="Fecha de Zarpe", compute="compute_departure_date")

    shipping_number = fields.Integer(string="Número Embarque", compute="compute_shipping_number")

    partner_id = fields.Many2one('res.partner')

    def compute_ships(self):
        for item in self:
            item.ship_ids = item.picking_ids.mapped('ship') 
    
    def compute_ordered_quantity(self):
        for item in self:
            item.ordered_quantity = item.order_line[0].product_uom_qty

    def compute_delivered_quantity(self):
        for item in self:
            item.delivered_quantity = item.order_line[0].qty_delivered

    def compute_unit_price(self):
        for item in self:
            item.unit_price = item.order_line[0].price_unit

    def compute_departure_date(self):
        for item in self:
            item.departure_date = item.picking_ids[0].departure_date

    def compute_departure_date(self):
        for item in self:
            item.compute_shipping_number = item.picking_ids[0].compute_shipping_number

