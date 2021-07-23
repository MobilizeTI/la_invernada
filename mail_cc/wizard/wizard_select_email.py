from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class WizardSelectEmail(models.TransientModel):

    _name = 'wizard.select.email'
    _description = 'Asistente para seleccionar email en plantilla de correo'
    
    partner_ids = fields.Many2many('res.partner', 
        'wizard_select_email_res_partner_rel', 
        'wizard_id', 'partner_id', 'Email',)
    
    @api.multi
    def action_process(self):
        active_ids = self.env.context.get('active_ids') or []
        field_name = self.env.context.get('field_name') or 'email_bcc'
        templates = self.env['mail.template'].browse(active_ids)
        templates.write({field_name: ",".join(self.partner_ids.mapped('email'))})
        return {'type': 'ir.actions.act_window_close'}
