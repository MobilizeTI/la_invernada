from odoo import fields, models, api
import json
from odoo.tools import date_utils


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_number = fields.Char('Contrato Interno')

    ship_ids = fields.Many2many('custom.ship', string="Nave", compute="_compute_ships")

    ordered_quantity = fields.Float(string="Cantidad Pedida", compute="_compute_ordered_quantity")

    delivered_quantity = fields.Float(string="Cantidad Entregada", compute="_compute_delivered_quantity")

    unit_price = fields.Float(string="Precio Unitario", compute="_compute_unit_price")

    departure_date = fields.Datetime(string="Fecha de Zarpe", compute="_compute_departure_date")

    shipping_number = fields.Char(string="Número Embarque", compute="_compute_shipping_number")

    partner_id = fields.Many2one('res.partner', "Cliente", readonly=False)

    is_current_company = fields.Boolean(compute="_compute_company_id")

    client_contact = fields.Char('Contrato Cliente')

    def _compute_company_id(self):
        #for item in self:
            if self.env.context.get('uid', False):
                item.current_company_id = self.env.context.get('uid', False)
            else:
                item.current_company_id = False

    def _compute_ships(self):
        for item in self:
            item.ship_ids = item.picking_ids.mapped('ship')

    def _compute_ordered_quantity(self):
        for item in self:
            item.ordered_quantity = item.order_line[0].product_uom_qty

    def _compute_delivered_quantity(self):
        for item in self:
            item.delivered_quantity = item.order_line[0].qty_delivered

    def _compute_unit_price(self):
        for item in self:
            item.unit_price = item.order_line[0].price_unit

    def _compute_departure_date(self):
        #valid if one dispatch of sale order havent date
        for item in self:
            if len(item.picking_ids) > 0:
                item.departure_date = item.picking_ids[0].departure_date

    def _compute_shipping_number(self):
        for item in self:
            shipping_number = ""
            for picking in item.picking_ids:
                if picking.shipping_number and picking.shipping_number != 0:
                    shipping_number = str(picking.shipping_number)
                    break
            item.shipping_number = shipping_number

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for pick in self.picking_ids:
            pick.clean_reserved()
        return res

