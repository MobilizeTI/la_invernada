from odoo import fields, models, api


class StockProductionLotSerial(models.Model):
    _name = 'stock.production.lot.serial'

    name = fields.Char(
        'Serie',
        compute='_compute_name'
    )

    calculated_weight = fields.Float('Peso Estimado')

    real_weight = fields.Float(
        'Peso Real',
        nulable=True,
        default=None
    )

    display_weight = fields.Float(
        'Peso',
        compute='_compute_display_weight',
        inverse='_inverse_real_weight'
    )

    stock_production_lot_id = fields.Many2one(
        'stock.production.lot',
        'Lote'
    )

    serial_number = fields.Char(
        'Serie'
    )

    @api.multi
    def _compute_display_weight(self):
        for item in self:
            if item.real_weight:
                item.display_weight = item.real_weight
            else:
                item.display_weight = item.calculated_weight

    @api.multi
    def _inverse_real_weight(self):
        for item in self:
            item.real_weight = item.display_weight

    @api.multi
    def _compute_name(self):
        for item in self:
            item.name = item.serial_number
