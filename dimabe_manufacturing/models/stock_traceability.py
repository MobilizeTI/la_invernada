from odoo import fields, models, api


class StockTraceability(models.Model):
    _inherit = 'stock.traceability'

    @api.model
    def get_lines(self, line_id=None, **kw):
        context = dict(self.env.context)
        models._logger.error('context {}'.format(self.env.context))
        model = kw and kw['model_name'] or context.get('model')
        rec_id = kw and kw['model_id'] or context.get('active_id')
        level = kw and kw['level'] or 1
        models._logger.error('{} {} {}'.format(model, rec_id, level))
        lines = self.env['stock.move.line']
        models._logger.error('lines {}'.format(lines))
        move_line = self.env['stock.move.line']
        models._logger.error('move_line {}'.format(move_line))
        if rec_id and model == 'stock.production.lot':
            lines = move_line.search([
                ('lot_id', '=', context.get('lot_name') or rec_id),
                ('state', '=', 'done'),
            ])
            models._logger.error('entró lot')
        elif rec_id and model == 'stock.move.line' and context.get('lot_name'):
            models._logger.error('entro move_line')
            record = self.env[model].browse(rec_id)
            models._logger.error('record {}'.format(record))
            dummy, is_used = self._get_linked_move_lines(record)
            models._logger.error('{} {}'.format(dummy, is_used))
            if is_used:
                lines = is_used
        elif rec_id and model in ('stock.picking', 'mrp.production'):
            record = self.env[model].browse(rec_id)
            if model == 'stock.picking':
                lines = record.move_lines.mapped('move_line_ids').filtered(lambda m: m.lot_id and m.state == 'done')
            else:
                lines = record.move_finished_ids.mapped('move_line_ids').filtered(lambda m: m.state == 'done')
        move_line_vals = self._lines(line_id, model_id=rec_id, model=model, level=level, move_lines=lines)
        final_vals = sorted(move_line_vals, key=lambda v: v['date'], reverse=True)
        lines = self._final_vals_to_lines(final_vals, level)
        return lines