from odoo import fields, models, api


class DriedOven(models.Model):
    _name = 'dried.oven'
    _description = 'horno de secado'

    name = fields.Char('Horno')



