from odoo import models, fields, api

class CustomFreightPaymentTerm(models.Model):

    _name = 'custom.freight.payment.term'

    name = fields.Char(string= 'Nombre', required=True)
