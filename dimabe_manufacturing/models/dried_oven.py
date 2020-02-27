from odoo import fields, models, api
from datetime import datetime


class DriedOven(models.Model):
    _name = 'dried.oven'
    _description = 'horno de secado'

    name = fields.Char('Horno')

    @api.onchange('name')
    def onchange_name(self):
        self.name = str.upper(self.name)
