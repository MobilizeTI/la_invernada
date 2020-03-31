from odoo import fields, models, api
from odoo.addons import decimal_precision as dp


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    total_reserved = fields.Float(
        'Total Reservado',
        compute='_compute_total_reserved',
        digits=dp.get_precision('Product Unit of Measure')
    )

    @api.multi
    def _compute_total_reserved(self):
        for item in self:
            item.total_reserved = sum(item.lot_id.stock_production_lot_serial_ids.filtered(
                lambda a: (a.reserved_to_production_id or a.reserved_to_stock_picking_id) and (
                    a.reserved_to_production_id.state not in ['done', 'cancel'] or
                    a.reserved_to_stock_picking_id.state not in ['done', 'cancel']
                )
            ).mapped('display_weight'))
