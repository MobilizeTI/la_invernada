from odoo import models, api, fields
from dateutil.relativedelta import *
import pandas as pd
from odoo.addons import decimal_precision as dp


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    def test(self):
        for item in self:
            employee_id = item.contract_id.employee_id
            leaves = self.env['hr.leave'].search(
                [('employee_id', '=', employee_id.id), ('state', '=', 'validate')]).mapped('number_of_days')
            raise models.ValidationError(sum(leaves))
