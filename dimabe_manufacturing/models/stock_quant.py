from odoo import fields, models, api


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    total_reserved = fields.Float(
        'Total Reservado',
        compute='_compute_total_reserved'
    )

    @api.multi
    def _compute_total_reserved(self):
        for item in self:
            item.total_reserved = sum(item.lot_id.stock_production_lot_serial_ids.filtered(
                lambda a: not a.consumed and (a.reserved_to_production_id or a.reserved_to_stock_picking_id)
            ).mapped('display_weight'))
