from odoo import models, fields, api

class ResCurrency(models.Model):
    _inherit = 'res.currency'

    sii_currency_name = fields.Char(string="Nombre Moneda SII")