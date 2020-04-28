from odoo import models, fields

class DteType(models.Model):
    _name = 'dte.type'
    code = fields.Integer('Código')
    name = fields.Char('Nombre')