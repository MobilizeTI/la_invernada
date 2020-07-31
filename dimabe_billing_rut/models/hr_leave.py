from odoo import fields, models, api
from datetime import datetime, time

class HrLeave (models.Model):
    _inherit = 'hr.leave'

    def _get_number_of_days(self, date_from, date_to, employee_id):
        """ Returns a float equals to the timedelta between two dates given as string."""
        if employee_id:
            raise models.ValidationError(employee_id)
            employee = self.env['hr.employee'].browse(employee_id)
            return employee.get_work_days_data(date_from, date_to)['days']

        today_hours = self.env.user.company_id.resource_calendar_id.get_work_hours_count(
            datetime.combine(date_from.date(), time.min),
            datetime.combine(date_from.date(), time.max),
            False)

        return self.env.user.company_id.resource_calendar_id.get_work_hours_count(date_from, date_to) / (
                    today_hours or HOURS_PER_DAY)
    


