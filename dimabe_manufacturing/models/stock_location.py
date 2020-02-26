from odoo import fields, models


class StockLocation(models.Model):
    _inherit = 'stock.location'

    name = fields.Char('Nombre de Ubicación', readonly=True)
