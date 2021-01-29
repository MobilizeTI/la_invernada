from odoo import models, fields

class AccountIncoterms(models.Model):
    _inherit = 'account.incoterms'

    sii_code = fields.Char(string="Código SII")