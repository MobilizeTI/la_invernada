from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class MailTemplate(models.Model):
    _inherit = 'mail.template'
    
    email_bcc = fields.Char('Cco',
        help="Destinatarios para copias ocultas(Se pueden utilizar expresiones de campos)",)
    
    @api.multi
    def generate_email(self, res_ids, fields=None):
        if not fields:
            fields = ['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc', 'email_bcc','reply_to', 'scheduled_date']
        elif 'email_bcc' not in fields:
            fields.append('email_bcc')
        return super(MailTemplate, self).generate_email(res_ids, fields)
