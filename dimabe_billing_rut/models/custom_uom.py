from odoo import models, fields, api

class CustomUom(models.Model):

    _name = 'custom.uom'
    _rec_name = 'initials'

    name = fields.Char(string= 'Nombre', required=True)

    initials = fields.Char(string= 'Unidad Medida', required=True)

    code = fields.Char(string= 'Código', required=True)