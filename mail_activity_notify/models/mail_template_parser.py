from odoo import models, api, fields, tools

class EmailMailActivitiesTodo(models.AbstractModel):

    _inherit = 'mail.template.parser'
    _name = 'mail.view_et_activities_todo.parser'
    
    @api.model
    def get_values(self, template, record):
        values = super(EmailMailActivitiesTodo, self).get_values(template, record)
        values['activity_overdue'] = self.env.context.get('activity_overdue') or []
        values['activity_today'] = self.env.context.get('activity_today') or []
        values['activity_planned'] = self.env.context.get('activity_planned') or []
        values['user_to_notify'] = self.env.context.get('user') or self.env.user
        return values
