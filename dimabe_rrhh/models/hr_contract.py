from odoo import fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    data_id = fields.Many2one('custom.data', 'Tramo Asignacion Familiar')

    company_logon_id = fields.Many2one(
        'res.company',
        string='company',
        defualt=lambda self: self.env.user.company_id)
