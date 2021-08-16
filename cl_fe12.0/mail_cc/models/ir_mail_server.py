from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class IrMailServer(models.Model):
    _inherit = 'ir.mail_server'
    
    def build_email(self, email_from, email_to, subject, body, email_cc=None, email_bcc=None, reply_to=False,
                    attachments=None, message_id=None, references=None, object_id=False, subtype='plain', headers=None,
                    body_alternative=None, subtype_alternative='plain'):
        if message_id:
            message_rec = self.env['mail.message'].search([('message_id','=',message_id)], limit=1)
            if message_rec:
                if message_rec.email_bcc:
                    if email_bcc:
                        email_bcc.extend(tools.email_split(message_rec.email_bcc))
                    else:
                        email_bcc = tools.email_split(message_rec.email_bcc)
                if message_rec.email_cc:
                    if email_cc:
                        email_cc.extend(tools.email_split(message_rec.email_cc))
                    else:
                        email_cc = tools.email_split(message_rec.email_cc)
        return super(IrMailServer, self).build_email(email_from, email_to, subject, body, email_cc=email_cc, email_bcc=email_bcc, reply_to=reply_to,
                    attachments=attachments, message_id=message_id, references=references, object_id=object_id, subtype=subtype, headers=headers,
                    body_alternative=body_alternative, subtype_alternative=subtype_alternative)
