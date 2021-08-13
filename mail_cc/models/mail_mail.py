from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class MailMail(models.Model):
    _inherit = 'mail.mail'
    
    email_bcc = fields.Char('Cco', 
        help='Destinatarios en copia oculta')
