from odoo import models, api, fields, tools


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'
    
    def _message_log(self, body='', subject=False, message_type='notification', **kwargs):
        # cuando el usuario no tenga correo, usar el correo generico
        # para evitar errores y se detengan procesos x falta de correo
        # y pasar por context ese correo con la clave email_from_to_message_log 
        if not self.env.user.email:
            email = self.env['mail.message']._get_default_from_ec()
            return super(MailThread, self.with_context(email_from_to_message_log=email))._message_log(body, subject, message_type, **kwargs)
        return super(MailThread, self)._message_log(body, subject, message_type, **kwargs)

    def message_notify(self, partner_ids, body='', subject=False, **kwargs):
        # cuando el usuario no tenga correo, usar el correo generico
        # para evitar errores y se detengan procesos x falta de correo
        # y pasar por context ese correo con la clave email_from_to_message_log 
        if not self.env.user.email:
            email = self.env['mail.message']._get_default_from_ec()
            return super(MailThread, self.with_context(email_from_to_message_log=email)).message_notify(partner_ids, body, subject, **kwargs)
        return super(MailThread, self).message_notify(partner_ids, body, subject, **kwargs)
