from odoo import models, fields, api

class AccountInvoiceObservations(models.Model):
    _inherit = 'account.invoice.observations'

    observations = []