from odoo import fields, models, api,_
from odoo.exceptions import UserError, ValidationError
from odoo.tools.pycompat import izip
from odoo.tools.float_utils import float_round, float_compare, float_is_zero
from odoo.addons import decimal_precision as dp


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    count_stock_production_lot_serial = fields.Integer(
        'Total Bultos',
        compute='_compute_count_stock_production_lot_serial'
    )

    is_raw = fields.Boolean('Es Subproducto')

    tmp_qty_done = fields.Float(
        'Realizado',
        digits=dp.get_precision('Product Unit of Measure')
    )

    sale_order_id = fields.Many2one('sale.order','Orden')

    @api.multi
    def _compute_count_stock_production_lot_serial(self):
        for item in self:
            if item.lot_id:
                item.count_stock_production_lot_serial = len(item.lot_id.stock_production_lot_serial_ids)

    def _action_done(self):
        for item in self:
            if item.location_dest_id.id == 7:
                item.update({
                    'state': 'done'
                })
            else:
                res = super(StockMoveLine, self)._action_done()
                return res

    def unlink(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for ml in self:
            if ml.state in ('done', 'cancel'):
                raise UserError(_('You can not delete product moves if the picking is done. You can only correct the done quantities.'))
            # Unlinking a move line should unreserve.
            if ml.product_id.type == 'product' and not ml.location_id.should_bypass_reservation() and not float_is_zero(ml.product_qty, precision_digits=precision):
                raise UserError("Cago")
                self.env['stock.quant']._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
        moves = self.mapped('move_id')
        res = super(StockMoveLine, self).unlink()
        if moves:
            moves._recompute_state()
        return res