from odoo import models, api, fields

class PurchaseOrderLine(models.Model):
    _inherit = ["purchase.order.line"]

    @api.multi
    def _get_stock_move_price_unit(self):
        #reemplazar funcion para pasar el precio con descuento al movimiento de stock
        self.ensure_one()
        line = self[0]
        order = line.order_id
        price_unit = line._get_price_unit_final()
        if line.taxes_id:
            price_unit = line.taxes_id.with_context(round=False).compute_all(
                price_unit, currency=line.order_id.currency_id, quantity=1.0, product=line.product_id, partner=line.order_id.partner_id
            )['total_excluded']
        if line.product_uom.id != line.product_id.uom_id.id:
            price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
        if order.currency_id != order.company_id.currency_id:
            price_unit = order.currency_id._convert(
                price_unit, order.company_id.currency_id, self.company_id, self.date_order or fields.Date.today(), round=False)
        return price_unit
