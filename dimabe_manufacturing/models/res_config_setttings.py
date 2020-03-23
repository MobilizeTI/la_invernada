from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    label_percent_subtract = fields.Float(
        '% peso Etiqueta',
        digits=dp.get_precision('% peso Etiqueta'),
        default=0.3
    )

    label_percent_subtract_value = fields.Float(
        'Valor a Calcular',
        compute='_compute_label_percent_subtract_value',
        store=True
    )

    @api.multi
    @api.depends('label_percent_subtract')
    def _compute_label_percent_subtract_value(self):
        for item in self:
            item.label_percent_subtract_value = item.label_percent_subtract / 100
