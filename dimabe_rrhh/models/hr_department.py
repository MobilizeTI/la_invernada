from odoo import fields, models


class HrContract(models.Model):
    _inherit = 'hr.department'
    analytic_account_id = fields.Many2one('account.analytic.account', 'Centro de Costos')