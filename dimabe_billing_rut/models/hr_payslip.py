from odoo import models,api,fields

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    def test(self):
        for item in self:
            employee_id = item.contract_id.employee_id
            leaves = self.env['hr.leave'].search([('employee_id','=',employee_id.id)])
            raise models.ValidationError(leaves)