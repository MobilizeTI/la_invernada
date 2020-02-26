from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    stock_move_line_lot_ids = fields.One2many(
        'stock.move.line',
        string='Detalle',
        compute='_compute_stock_move_line_lot_ids'
    )
    @api.multi
    def _compute_stock_move_line_lot_ids(self):
        for item in self:
            if item.get_mp_move():
                item.stock_move_line_lot_ids = item.get_mp_move().move_line_ids
