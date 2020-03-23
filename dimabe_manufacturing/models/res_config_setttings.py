from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    label_percent_subtract = fields.Float(
        '% peso Etiqueta',
        digits=dp.get_precision('Product Unit of Measure'),
        default=0.3
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
