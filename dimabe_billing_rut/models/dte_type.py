from odoo import models, fields

class DteType(models.Model):
    _name = 'dte.type'
    code = fields.Char('Código')
    name = fields.Char('Nombre')