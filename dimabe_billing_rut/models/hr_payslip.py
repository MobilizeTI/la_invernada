from odoo import models, api, fields
from dateutil.relativedelta import *
import pandas as pd
from odoo.addons import decimal_precision as dp


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    def get_leave(self):
        for item in self:
            employee_id = item.contract_id.employee_id
            leaves = self.env['hr.leave'].search(
                [('employee_id', '=', employee_id.id), ('state', '=', 'validate')]).mapped('number_of_days')
            self.env['hr.payslip.worked_days'].create({
                'contract_id': item.contract_id.id,
                'code':'ABSC100',
                'number_of_days':sum(leaves),
                'payslip_id':item.id
            })
