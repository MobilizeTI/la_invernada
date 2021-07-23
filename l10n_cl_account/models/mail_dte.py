from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class MailMessageDteDocument(models.Model):
    _inherit = 'mail.message.dte.document'
    
    @api.multi
    def action_accept_document_preview(self):
        return self.env['odoo.utils'].show_wizard('wizard.accept.document.xml', 'wizard_accept_document_xml_form_view', 'Aceptar Documento')
