from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    label_percent_subtract = fields.Float(
        '% peso Etiqueta',
        digits=dp.get_precision('% peso Etiqueta')
    )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('dimabe_manufacturing.label_percent_subtract', float(self.label_percent_subtract))

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res['label_percent_subtract'] = float(get_param('dimabe_manufacturing.label_percent_subtract'))
        return res

    # label_percent_subtract_value = fields.Float(
    #     'Valor a Calcular',
    #     compute='_compute_label_percent_subtract_value',
    #     store=True
    # )
    #
    # @api.multi
    # @api.depends('label_percent_subtract')
    # def _compute_label_percent_subtract_value(self):
    #     for item in self:
    #         item.label_percent_subtract_value = item.label_percent_subtract / 100
