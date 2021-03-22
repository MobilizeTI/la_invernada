from odoo import models, fields, api

class CustomQualityType(models.Model):

    _name = 'custom.quality.type'

    name = fields.Char(string= 'Nombre', required=True)