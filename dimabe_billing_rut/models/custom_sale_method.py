from odoo import models, fields, api

class CustomSaleMethod(models.Model):

    _name = 'custom.sale.method'

    name = fields.Char(string= 'Nombre', required=True)

    initials = fields.Char(string= 'Sigla', required=True)

    code = fields.Char(string= 'Código', required=True)