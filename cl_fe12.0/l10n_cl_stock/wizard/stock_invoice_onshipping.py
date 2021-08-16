from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class StockInvoiceOnshipping(models.TransientModel):
    _inherit = 'stock.invoice.onshipping'

    journal_document_class_id = fields.Many2one('account.journal.sii_document_class', 'Tipo Documento SII')
    use_documents = fields.Boolean(
        string='Use Documents?',
        related='journal_id.use_documents'
    )
    
    @api.onchange('journal_id', 'invoice_type')
    def _onchange_journal_id(self):
        domain = {}
        warning = {}
        if not self.journal_id.use_documents:
            return {'domain': domain, 'warning': warning}
        domain_journal = [
            ('journal_id', '=', self.journal_id.id),
        ]
        if self.invoice_type in ['in_refund', 'out_refund']:
            domain_journal.append(('sii_document_class_id.document_type','in',['credit_note']))
        elif self.invoice_type == 'in_invoice':
            domain_journal.append(('sii_document_class_id.document_type','=', 'invoice_in'))
        else:
            domain_journal.append(('sii_document_class_id.document_type','=', 'invoice'))
        domain['journal_document_class_id'] = domain_journal
        # buscar el primer registro para pasarlo por defecto
        # pero agregar que sea electronico
        if not self.journal_document_class_id:
            self.journal_document_class_id = self.env['account.journal.sii_document_class'].search(domain_journal+ [('sii_document_class_id.dte', '=', True)], limit=1).id
        return {'domain': domain, 'warning': warning}

    @api.multi
    def _build_invoice_values_from_pickings(self, pickings):
        values = super(StockInvoiceOnshipping, self)._build_invoice_values_from_pickings(pickings)
        picking = fields.first(pickings)
        referencias = []
        if self.use_documents and picking.move_reason in ('1', '5') and picking.document_class_id: # venta y traslado interno
            date_invoice = self.invoice_date or fields.Date.context_today(self)
            if picking.date_done:
                date_invoice = fields.Datetime.context_timestamp(self, picking.date_done)
            referencias = [(0,0, {
                'origen': int(picking.sii_document_number),
                'sii_referencia_TpoDocRef': picking.document_class_id.id,
                'fecha_documento': date_invoice.strftime(DF),
            })]
        values.update({
            'journal_document_class_id': self.journal_document_class_id.id,
            'referencias': referencias,
        })
        return values
    
    @api.multi
    def _get_invoice_line_values(self, moves, invoice):
        values = super(StockInvoiceOnshipping, self)._get_invoice_line_values(moves, invoice)
        move = fields.first(moves)
        move_sign = 1
        # en el stock.move pone la valoracion en negativo si el inventario sale de la bodega
        # asi que pasarlo a positivo
        if invoice.type in ('out_invoice', 'in_refund'):
            move_sign = -1
        values.update({
            'amount_cost': move.value * move_sign
        })
        if move.discount:
            values.update({
                'discount': move.discount,
            })
        if move.discount_value:
            values.update({
                'discount_value': move.discount_value,
            })
        return values
