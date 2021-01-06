from odoo import models, fields, api

class CustomReceivingCountryDte(models.Model):

    _name = 'custom.receiving.country.dte'

    name = fields.Char(string= 'Nombre', required=True)

    code = fields.Char(string= 'Código', required=True)