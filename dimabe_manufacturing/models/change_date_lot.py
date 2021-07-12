import datetime

from odoo import fields, models, api


class ChangeDateLot(models.TransientModel):
    _name = 'change.date.lot'

    lot_id = fields.Many2one('stock.production.lot', string='Lote')

    packaging_date_new = fields.Date(string='Fecha de Envasado')

    packaging_date_old = fields.Date(string='Fecha Actual')

    best_before_date_old = fields.Date(string='Fecha de Consumir Preferentemente antes de')

    best_before_date_new = fields.Date(string='Fecha de Consumir Preferentemente antes de')

    def change_pack(self):
        for item in self:
            item.lot_id.stock_production_lot_serial_ids.write({
                'packaging_date': item.packaging_date_new
            })
            item.lot_id.pallet_ids.write({
                'packaging_date': datetime.datetime.combine(item.packaging_date_new, datetime.datetime.min.time())
            })
            item.lot_id.write({
                'change_packaging': False
            })

    def change_best(self):
        for item in self:
            item.lot_id.stock_production_lot_serial_ids.write({
                'best_before_date_new': item.best_before_date_new
            })
            item.lot_id.write({
                'change_best': False
            })
