from odoo import models, fields, api

class CustomInvoiceObservations(models.Model):
    _name = 'custom.invoice.observations'

    observations = fields.char(
        'Observación',
        nullable = True,
        default= None,
        size=140
    )