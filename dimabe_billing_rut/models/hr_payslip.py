from odoo import models,api,fields

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    def test(self):
        for item in self:
            raise models.ValidationError(item.contract_id)