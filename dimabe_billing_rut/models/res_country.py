from odoo import models, fields, api

class ResCountry(models.Model):
    _inherit = 'res.country'

    sii_code = fields.Char(string="Código SII")