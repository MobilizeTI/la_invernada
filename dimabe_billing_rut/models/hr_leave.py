from odoo import fields, models, api
from datetime import datetime, time
from dateutil.relativedelta import *
import pandas as pd
from odoo.addons import decimal_precision as dp

class HrLeave (models.Model):
    _inherit = 'hr.leave'

    @api.multi
    @api.depends('number_of_days')
    def _compute_number_of_days_display(self):
        for holiday in self:
            days = holiday.request_date_to - holiday.request_date_from
            saturdays = pd.date_range(start=holiday.request_date_from, end=holiday.request_date_to, freq='W-SAT').strftime(
                '%m/%d/%Y').tolist()
            sundays = pd.date_range(start=holiday.request_date_from, end=holiday.request_date_to, freq='W-SUN').strftime(
                '%m/%d/%Y').tolist()
            holiday.number_of_days_display = days.days - (len(saturdays) + len(sundays))

    @api.onchange('date_from', 'date_to', 'employee_id')
    def _onchange_leave_dates(self):
        if self.date_from and self.date_to:
            days = self.request_date_to - self.request_date_from
            saturdays = pd.date_range(start=self.request_date_from, end=self.request_date_to,
                                      freq='W-SAT').strftime(
                '%m/%d/%Y').tolist()
            sundays = pd.date_range(start=self.request_date_from, end=self.request_date_to,
                                    freq='W-SUN').strftime(
                '%m/%d/%Y').tolist()
            self.number_of_days =  days.days - (len(saturdays) + len(sundays))
        elif self.request.unit_half:
            self.number_of_days = 0.5
        else:
            self.number_of_days = 0
    


