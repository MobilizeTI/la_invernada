from odoo import models, fields

class account_invoice_references(models.Model):
    _name = 'account.invoice.references'
    _description = 'Referencias de un DTE'

    document_type_reference_id = fields.Many2one('dte.type', string="Tipo Documento Referencia")
    code_reference = fields.Selection(
            [
                ('1', 'Anula Documento de Referencia'),
                ('2', 'Corrige texto Documento Referencia'),
                ('3', 'Corrige montos')
            ],
            string="Tipo referencia",
        )
    reason = fields.Char(
            string="Motivo",
        )
    folio_reference = fields.Text(
            string="Numero Documento referencia",
            required=True,
        )
    document_date = fields.Date(
            string="Fecha Documento",
            required=True,
    )
    invoice_id = fields.Many2one(
        'account.invoice',
        ondelete='cascade',
        index=True,
        copy=False,
        string="Documento",
    )