from odoo import models, fields, api

class AccountInvoiceReferences(models.Model):
    _name = 'account.invoice.references'

    line_number = fields.Integer('Linea')

    type_doc = fields.Integer('Tipo Documento')

    folio_ref = fields.Char('Folio')

    date_ref = fields.Date('Fecha')

    code_ref = fields.Integer('Código')

    razon_ref = fields.Char('Razón Referencia')