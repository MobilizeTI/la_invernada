from odoo import models, fields

class CustomPackageType(models.Model):
    _name = 'custom.package.type'

    code = fields.Char(string= 'Código', required=True)

    name = fields.Char(string= 'Nombre', required=True)

    short_name = fields.Char(string= 'Nombre Corto', required=True)


   