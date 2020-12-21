from odoo import models, fields, api

class AccountInvoiceReferences(models.Model):
    _inherit = 'account.invoice.references'

    line_number = fields.Integer()
    type_doc = fields.Integer()
    folio_ref = fields.Char()
    date_ref = fields.Date()
    code_ref = fields.Integer()
