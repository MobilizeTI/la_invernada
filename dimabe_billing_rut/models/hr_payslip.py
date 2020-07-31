from odoo import models, api, fields
from dateutil.relativedelta import *
import pandas as pd
from odoo.addons import decimal_precision as dp
import re


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    def get_leave(self):
        for item in self:
            employee_id = item.contract_id.employee_id
            leaves = self.env['hr.leave'].search(
                [('employee_id', '=', employee_id.id), ('state', '=', 'validate')])
            for leave in leaves:
                if leave.holiday_status_id.name in item.worked_days_line_ids.mapped('name'):
                    item.worked_days_line_ids.filtered(lambda a: a.name == leave.holiday_status_id.name).update(
                        {
                            'number_of_days': leave.number_of_days
                        }
                    )
                else:
                    self.env['hr.payslip.worked_days'].create({
                        'name': leave.holiday_status_id.name,
                        'number_of_days': leave.number_of_days,
                        'code': '',
                        'contract_id': item.contract_id.id,
                        'payslip_id': item.id
                    })
