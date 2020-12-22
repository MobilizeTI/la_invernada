from odoo import models, fields, api

class AccountInvoiceObservations(models.Model):
    _name = 'account.invoice.observations'

    observations = fields.text(
        'Observación',
        nullable = True,
        default= None
    )