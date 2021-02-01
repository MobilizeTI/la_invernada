from odoo import models, fields, api

class CustomCities(models.Model):
    _name = ('custom.cities')

    _rec_name = 'city_country'

    name = fields.Char(string="Ciudad")

    country = fields.Many2one('res.country',string="País")

    city_country = fields.Char(string="Ciudad, País", compute='_compute_fields_city_country')

    @api.depends('name','country')
    def _compute_fields_city_country(self):
        for item in self:
            item.city_country = item.name + ', ' +  item.country.name
