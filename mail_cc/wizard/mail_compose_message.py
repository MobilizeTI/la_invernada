from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'
    
    select_mail_from_partner = fields.Boolean('Seleccionar Cuentas de email?')
    partner_mail_cc_ids = fields.Many2many('res.partner', 
        'mail_compose_message_res_partner_cc_rel', 'wizard_id', 'partner_id', 'Cc',)
    partner_mail_bcc_ids = fields.Many2many('res.partner', 
        'mail_compose_message_res_partner_bcc_rel', 'wizard_id', 'partner_id', 'Cco',)
    
    @api.model
    def generate_email_for_composer(self, template_id, res_ids, fields=None):
        if not fields:
            fields = ['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc', 'email_bcc',  'reply_to', 'attachment_ids', 'mail_server_id']
        elif 'email_bcc' not in fields:
            fields.append('email_bcc')
        return super(MailComposeMessage, self).generate_email_for_composer(template_id, res_ids, fields)
    
    @api.multi
    def get_mail_values(self, res_ids):
        values = super(MailComposeMessage, self).get_mail_values(res_ids)
        if self.email_bcc or self.email_cc:
            for res_id, vals  in values.items():
                if self.email_bcc:
                    vals.update({'email_bcc': self.email_bcc})
                if self.email_cc:
                    vals.update({'email_cc': self.email_cc})
        return values
    
    @api.onchange('partner_mail_cc_ids',)
    def _onchange_partner_mail_cc(self):
        self.email_cc = ",".join(self.partner_mail_cc_ids.mapped('email'))
        
    @api.onchange('partner_mail_bcc_ids',)
    def _onchange_partner_mail_bcc(self):
        self.email_bcc = ",".join(self.partner_mail_bcc_ids.mapped('email'))
