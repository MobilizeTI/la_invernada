from odoo import models, api, fields, tools
from email.utils import formataddr


class MailMessage(models.Model):
    _inherit = 'mail.message'
    
    #reemplazar campo para cambiar default qe esta como referencia para hacerla lambda
    email_from = fields.Char(default=lambda self: self._get_default_from(),)
    #agregar campo para copias en carbon
    email_cc = fields.Char('Cc', help='Destinatarios en copia carbon')
    #agregar campo para copias ocultas
    email_bcc = fields.Char(u'Cco', help='Destinatarios en copia oculta')
    
    @api.model
    def _get_default_from_ec(self):
        email = self.env['ir.config_parameter'].sudo().get_param('default_email_from', False)
        if not email:
            email = tools.config.get('email_from')
        if not email:
            email = "info@blaze-otp.com"
        return email
        
    @api.model
    def _get_default_from(self):
        # cuando el usuario no tenga correo, usar el correo generico
        # para evitar errores y se detengan procesos x falta de correo
        if not self.env.user.email:
            email = self._get_default_from_ec()
            return formataddr((self.env.user.name, email))
        return super(MailMessage, self)._get_default_from()
