from odoo import models, api, fields, tools
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

class AccountInvoice(models.Model):

    _inherit = 'account.invoice'
    
    @api.multi
    def _prepare_referencias_from_invoice(self):
        return {
            'origen': int(self.sii_document_number or self.reference),
            'sii_referencia_TpoDocRef': self.document_class_id.id,
            'sii_referencia_CodRef': '3',
            'motivo': "Corrige montos",
            'fecha_documento': self.date_invoice
        }
    
    @api.onchange('purchase_id')
    def purchase_order_change(self):
        warehouse_id = False
        if self.purchase_id:
            warehouse_id = self.purchase_id.warehouse_id.id
            self.date_invoice = fields.Datetime.context_timestamp(self, self.purchase_id.date_order).strftime(DF)
            if self.type == 'in_refund':
                referencias = self.env['account.invoice.referencias']
                for invoice in self.purchase_id.invoice_ids.filtered(lambda x: x.type == 'in_invoice'):
                    data = invoice._prepare_referencias_from_invoice()
                    new_line = referencias.new(data)
                    referencias += new_line
                self.referencias += referencias
        res = super(AccountInvoice, self).purchase_order_change()
        if warehouse_id:
            self.warehouse_id = warehouse_id
        return res
    
    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        payment_term_id = self.env.context.get('from_purchase_order_change') and self.payment_term_id or False
        res = super(AccountInvoice, self)._onchange_partner_id()
        if payment_term_id:
            self._onchange_payment_term_date_invoice()
        return res
    
    def _prepare_invoice_line_from_po_line(self, line):
        vals = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(line)
        # cuando la politica de facturacion en compras sea cantidad pedida
        # y hacer una NC, pasar la cantidad recibida menos lo facturado
        # ignorar la politica de facturacion
        if self.type == 'in_refund' and line.product_id.purchase_method == 'purchase':
            if line.qty_invoiced > line.qty_received:
                vals['quantity'] = line.qty_invoiced - line.qty_received
        return vals