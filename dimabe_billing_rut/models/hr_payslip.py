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
                models._logger.error(leaves.holiday_status_id.name)




