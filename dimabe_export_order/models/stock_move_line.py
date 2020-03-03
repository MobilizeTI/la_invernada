from odoo import fields, models, api


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    lot_serial = fields.Many2many('stock_production_lot_serial', compute='get_serial')

    @api.multi
    def get_serial(self):
        for item in self:
            if item.lot_id:
                for serial in item.stock_production_lot_serial_ids:
                    models._logger.error(serial.id)
