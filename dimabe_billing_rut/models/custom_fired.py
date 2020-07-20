from odoo import models, fields, api


class CustomFired(models.Model):
    _name = 'custom.fired'

    name = fields.Char('Nombre', required=True)

    description = fields.Text('Descripcion', required=True)

    article = fields.Selection([
        ('159','Articulo 159'),
        ('160','Articulo 160'),
        ('161','Articulo 161')
    ])


