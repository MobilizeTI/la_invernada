from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

class AccountInvoice(models.Model):

    _inherit = 'account.invoice'
    
    @api.one
    @api.constrains('journal_document_class_id', 'state')
    def _check_pos_session_open(self):
        # evitar emitir documentos si hay una sesion del pos abierta
        # con el tipo de documento(y secuencia) de la factura
        if not self.env.context.get('skip_validation_invoice_pos', False) and self.journal_document_class_id and self.journal_document_class_id.sii_document_class_id.sii_code in ('33', 33) and self.journal_document_class_id.sequence_id and self.state != 'cancel':
            pos_sessions = self.env['pos.session'].search([
                ('state', '!=', 'closed'),
            ])
            for pos_session in pos_sessions:
                if pos_session.document_available_ids.filtered(lambda x: x.sequence_id == self.journal_document_class_id.sequence_id):
                    raise ValidationError('Hay sessiones abiertas en el Punto de Venta: %s, ' \
                                          'no se permite emitir documentos desde la parte administrativa ' \
                                          'porque podrian duplicarse los documentos, ' \
                                          'primero cierre sesion en los Puntos de venta' % (pos_session.config_id.name))
