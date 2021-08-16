from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class StockMove(models.Model):
    _inherit = 'stock.move'
    
    @api.multi
    def _get_price_unit(self):
        """ Returns the unit price for the move"""
        #reemplazar funcion para pasar el precio con descuento al movimiento de stock
        self.ensure_one()
        if self.purchase_line_id and self.product_id.id == self.purchase_line_id.product_id.id:
            line = self.purchase_line_id
            order = line.order_id
            price_unit = line._get_price_unit_final()
            if line.taxes_id:
                price_unit = line.taxes_id.with_context(round=False).compute_all(price_unit, currency=line.order_id.currency_id, quantity=1.0)['total_excluded']
            if line.product_uom.id != line.product_id.uom_id.id:
                price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
            if order.currency_id != order.company_id.currency_id:
                price_unit = order.currency_id._convert(
                    price_unit, order.company_id.currency_id, order.company_id, self.date, round=False)
            return price_unit
        return super(StockMove, self)._get_price_unit()

    def _action_cancel(self):
        res = super(StockMove, self)._action_cancel()
        self.mapped('purchase_line_id').sudo()._update_received_qty()
        return res
    