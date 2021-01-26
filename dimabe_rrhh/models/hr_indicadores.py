from odoo import models, fields, api


class HrIndicatores(models.Model):
    _inherit = 'hr.indicadores'

    multuality_ids = fields.One2many('custom.mutuality', 'indicator_id', string='Valores por Compañia')
