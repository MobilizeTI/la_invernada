from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    @api.model
    def _prepate_move_vals_from_pos(self, pos_line_vals, picking, location, location_dest):
        move_vals = super(StockPicking, self)._prepate_move_vals_from_pos(pos_line_vals, picking, location, location_dest)
        product_model = self.env['product.product']
        product = product_model.browse(move_vals['product_id'])
        move_vals['discount'] = pos_line_vals.get('discount') or 0
        move_vals['discount_value'] = pos_line_vals.get('discount_value') or 0
        move_vals['precio_unitario'] = pos_line_vals.get('price_unit') or 0
        move_vals['move_line_tax_ids'] = [(6, 0, product.taxes_id.ids)]
        return move_vals
