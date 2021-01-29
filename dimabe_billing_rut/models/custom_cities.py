from odoo import models, fields

class CustomCities(models.Model):
    _name = ('custom.cities')

    name = fields.Char(string="Ciudad")

    country = fields.Many2one('res.country',string="País", nullable=True)
