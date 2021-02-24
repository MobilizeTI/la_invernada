from odoo import models, fields, api

class CustomSafeType(models.Model):

    _name = 'custom.safe.type'

    name = fields.Char(string= 'Nombre', required=True)
