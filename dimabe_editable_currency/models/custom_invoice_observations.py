from odoo import models, fields, api

class CustomInvoiceObservations(models.Model):
    _name = 'custom.invoice.observations'

    observations = fields.Char(
        string='Observación',
        nullable = True,
        default= None,
        size=140
    )

    invoice_id = fields.Many2one('account.invoice', auto_join = True)