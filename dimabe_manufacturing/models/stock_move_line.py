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
            raise models.ValidationError(f'{item.picking_id.is_multiple_dispatch or item.picking_id.picking_real_id or item.picking_id.picking_principal_id}')
            if item.location_dest_id.id == 7:
                item.update({
                    'state': 'done'
                })
            elif item.picking_id.is_multiple_dispatch or item.picking_id.picking_real_id or item.picking_id.picking_principal_id:

                item.write({
                    'state':'done'
                })
                item.lot_id.update_stock_quant(location_id=item.location_id.id)
            else:
                res = super(StockMoveLine, self)._action_done()
                return res
