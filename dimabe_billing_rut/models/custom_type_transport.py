from odoo import models, fields, api

class CustomTypeTransport(models.Model):

    _name = 'custom.type.transport'

    name = fields.Char(string= 'Nombre', required=True)

    code = fields.Char(string='Código', required=True)