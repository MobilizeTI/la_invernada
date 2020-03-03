from odoo import models, api


class StockTraceability(models.TransientModel):
    _inherit = 'stock.traceability.report'

    @api.model
    def _get_reference(self, move_line):

        res_model, res_id, ref = super(StockTraceability, self)._get_reference(move_line)

        if not res_model and not res_id and not ref:
            if move_line.lot_id:
                res_model = 'stock.production.lot'
                res_id = move_line.lot_id.id
                ref = move_line.lot_id.name
        return res_model, res_id, ref

    @api.model
    def _get_linked_move_lines(self, move_line):
        move_lines, is_used = super(StockTraceability, self)._get_linked_move_lines(move_line)
        if not move_lines and not is_used:
            move_lines = move_line.consume_line_ids
        return move_lines, is_used
