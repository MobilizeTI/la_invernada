from odoo import fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    data_id = fields.Many2one('custom.data', 'Tramo Asignacion Familiar')
