
from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
    warehouse_id = fields.Many2one('stock.warehouse', 'Tienda', 
        readonly=True, states={'draft':[('readonly',False)]})
    
    @api.multi
    def _can_split_document(self):
        return self.type in ('out_invoice', 'out_refund') and self.document_class_id and not self.ticket
    
    @api.multi
    def _get_number_lines(self):
        max_number_documents = self.env.user.company_id.max_number_documents
        if self.document_class_id.max_number_documents > 0:
            max_number_documents = self.document_class_id.max_number_documents
        return max_number_documents
    
    def _get_invoice_line_key_to_group(self, invoice_line):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        show_quantities_grouped = ICPSudo.get_param('show_quantities_grouped', default='show_detail')
        if show_quantities_grouped == 'show_grouped':
            company = self.env.user.company_id
            colors = []
            for atribute in invoice_line.product_id.attribute_value_ids.filtered(lambda x: x.attribute_id == company.color_id):
                colors.append(atribute.name)
            colors = ", ".join(colors)
            line_key = (invoice_line.product_id.product_tmpl_id, colors, invoice_line.discount, invoice_line.price_unit)
        else:
            line_key = (invoice_line.product_id, "", invoice_line.discount, invoice_line.price_unit)
        return line_key
    
    @api.model
    def _get_fields_to_split(self):
        fields_list = super(AccountInvoice, self)._get_fields_to_split()
        fields_list.extend([
            'warehouse_id', 'contact_id',
            'journal_document_class_id', 'acteco_id'
        ])
        return fields_list

    @api.multi
    def action_invoice_open(self):
        ctx = self.env.context.copy()
        for invoice in self:
            if invoice.type in ('in_refund', 'out_refund') and invoice.journal_id.use_documents and not invoice.referencias:
                raise UserError("Debe ingresar las referencias del documento anulado con Nota de Credito, por favor verifique el documento: %s" % invoice.display_name)
            #cuando sea NC que corrije texto, no mostrar mensaje de error
            # xq se puede agregar un producto comodin que no tenga impuestos
            if invoice.referencias.filtered(lambda x: x.sii_referencia_CodRef in ('1', '2')):
                ctx['skip_tax_validation'] = True
        return super(AccountInvoice, self.with_context(ctx)).action_invoice_open()

    @api.multi
    def action_update_account_analytic(self):
        self.ensure_one()
        analytic_model = self.env['account.analytic.default'].with_context(warehouse_id=self.warehouse_id.id)
        date = fields.Date.context_today(self)
        if self.date_invoice:
            date = self.date_invoice
        for invoice_line in self.invoice_line_ids:
            rec = analytic_model.account_get(invoice_line.product_id.id, self.partner_id.commercial_partner_id.id, self.env.uid, date, company_id=self.company_id.id)
            invoice_line.write({'account_analytic_id': rec.analytic_id.id})
        return True
    
    @api.one
    def _prepare_invoice_data(self, inv_type, journal_type, company):
        # pasar el tipo de documento sii correcto en entornos multicompany
        # esta funcion es llamada por el modulo enterprise de inter_company_rules
        invoice_vals = super(AccountInvoice, self)._prepare_invoice_data(inv_type, journal_type, company)[0]
        if invoice_vals.get('journal_id') and self.document_class_id:
            journal = self.env['account.journal'].browse(invoice_vals['journal_id'])
            journal_document_class = journal.journal_document_class_ids.filtered(lambda x: x.sii_document_class_id == self.document_class_id)
            if journal_document_class:
                invoice_vals['journal_document_class_id'] = journal_document_class[0].id
        return invoice_vals

