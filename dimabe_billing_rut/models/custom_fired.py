from odoo import models, fields, api


class CustomFired(models.Model):
    _name = 'custom.fired'

    name = fields.Char('Nombre', required=True)

    description = fields.Char('Descripcion', required=True)


