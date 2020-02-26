from odoo import fields, models


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    show_in_quality_report = fields.Boolean('Mostrar en Filtro Calidad')
