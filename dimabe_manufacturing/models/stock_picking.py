from odoo import models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def return_action(self):

        context = {
            'default_product_id': self.product.id,
            'default_product_uom_qty': self.quantity_done,
            'default_origin': self.name,
            'default_product_qty': self.quantity_done,
            'default_related_picking_id': self.id,
            'default_picking_ids': [(6, 0, [self.id])]
        }

        return {
            "type": "ir.actions.act_window",
            "res_model": "mrp.production",
            "view_type": "form",
            "view_mode": "form",
            "views": [(False, "form")],
            "view_id ref='mrp.mrp_production_form_view'": '',
            "target": "current",
            "context": context
        }
