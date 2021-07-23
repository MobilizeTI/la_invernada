from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _

class ResPartner(models.Model):

    _inherit = 'res.partner'
    
    @api.model
    def _notify_prepare_template_context(self, message, record, model_description=False, mail_auto_delete=True):
        values = super(ResPartner, self)._notify_prepare_template_context(message, record, model_description=model_description, mail_auto_delete=mail_auto_delete)
        values['show_no_response'] = self.env.context.get('show_no_response')
        return values