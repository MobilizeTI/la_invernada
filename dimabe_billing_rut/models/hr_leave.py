from odoo import fields, models, api
from datetime import datetime, time

class HrLeave (models.Model):
    _inherit = 'hr.leave'

    @api.multi
    @api.depends('number_of_days')
    def _compute_number_of_days_display(self):
        for holiday in self:
            days = holiday.request_date_from - request_date_to
            raise models.ValidationError(days)
            holiday.number_of_days_display =
    


