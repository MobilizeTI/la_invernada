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
        for ml in self:
            try:
                if ml.location_id.usage == 'production' and ml.location_dest_id.usage == 'production':
                    ml.write({
                        'state': 'done'
                    })
                else:
                    res = super(StockMoveLine,self)._action_done()
                    return res
            except UserError:
                ml.write({
                    'product_uom_qty':0,
                    'state':'done'
                })
                ml.lot_id.update_stock_quant(location_id=ml.location_id.id)

