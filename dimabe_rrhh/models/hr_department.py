from odoo import fields, models


class HrDepartment(models.Model):
    _inherit = 'hr.department'
    analytic_account_id = fields.Many2one('account.analytic.account', 'Centro de Costos',domain=[('company_id','=',2)])