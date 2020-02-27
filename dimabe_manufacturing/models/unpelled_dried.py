from odoo import fields, models, api


class UnpelledDried(models.Model):
    _name = 'unpelled.dried'
    _description = 'clase que para producción de secado y despelonado'

    name = fields.Char(
        'Proceso',
        compute='_compute_name'
    )

    producer_id = fields.Many2one(
        'res.partner',
        'Productor',
        domain=[('supplier', '=', True)]
    )

    in_lot_ids = fields.Many2many(
        'stock.production.lot',
        string='Lotes de Entrada'
    )

    out_lot_id = fields.Many2one(
        'stock.production.lot',
        'Lote Producción'
    )

    dried_oven_ids = fields.Many2many(
        'oven.use'
    )

    @api.multi
    def _compute_name(self):
        for item in self:
            item.name = item.out_lot_id.name
