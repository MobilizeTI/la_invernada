from odoo import models, api

class MailNotification(models.Model):
    _inherit = 'mail.notification'

    @api.model
    def get_signature_footer(self, user_id, res_model=None, res_id=None, context=None, user_signature=True):
        models._logger.error(res_model)
        if res_model is 'purchase.order':
            return ""

