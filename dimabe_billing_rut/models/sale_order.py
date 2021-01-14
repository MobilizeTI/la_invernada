from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'
   
    can_add_order = fields.Boolean(compute="_compute_sale_orders")

    def _compute_sale_orders(self):     
        for ol in self.order_line:
            if ol.qty_delivered < ol.product_uom_qty:
                return True
            else:
                return False 