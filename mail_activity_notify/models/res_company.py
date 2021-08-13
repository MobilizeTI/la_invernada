from collections import OrderedDict

from odoo import models, api, fields, tools

class ResCompany(models.Model):

    _inherit = 'res.company'
    
    @api.model
    def send_activities_todo(self):
        company = self.env.user.company_id
        activity_model = self.env['mail.activity']
        activity_todo = self.env.ref('mail.mail_activity_data_todo')
        activities = activity_model.search([('activity_type_id', '=', activity_todo.id)], order="date_deadline")
        activity_data = OrderedDict()
        for activity in activities:
            activity_data.setdefault(activity.user_id, {
                'activity_overdue': activity_model.browse(),
                'activity_today': activity_model.browse(),
                'activity_planned': activity_model.browse(),
            })
            if activity.state == 'overdue':
                activity_data[activity.user_id]['activity_overdue'] |= activity
            elif activity.state == 'today':
                activity_data[activity.user_id]['activity_today'] |= activity
            else:
                activity_data[activity.user_id]['activity_planned'] |= activity
        for user, activities in activity_data.items():
            if not user.email:
                continue
            if not activities['activity_overdue'] and not activities['activity_today'] and not activities['activity_planned']:
                continue
            template = self.env.ref('mail_activity_notify.et_activities_todo')
            ctx = self.env.context.copy()
            ctx['activity_overdue'] = activities['activity_overdue']
            ctx['activity_today'] = activities['activity_today']
            ctx['activity_planned'] = activities['activity_planned']
            ctx['email_to'] = user.email
            ctx['user'] = user
            template.with_context(ctx).action_sent_mail(company)
        return True