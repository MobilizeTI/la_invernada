from odoo import models, fields, api


class HrIndicadores(models.Model):
    _inherit = 'hr.indicadores'

    fonasa = fields.Float('Fonasa', required=True)

    pensiones_ips = fields.Float('Fondo de Pensiones', required=True)

    tope_imponible_salud = fields.Float('Tope Imponible Salud %', required=True)
