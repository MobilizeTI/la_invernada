from odoo import models, fields

class AccountIncoterms(models.Model):
    _inherit = 'account.incoterms'
    _rec_name = 'code'

    sii_code = fields.Char(string="Código SII")