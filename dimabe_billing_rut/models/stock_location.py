from odoo import models, fields

class StockLocation(models.Model):
    _inherit = 'stock.location'

    branch_code_sii = fields.Char(string = 'Código asignado por el SII')

    branch_address = fields.Char(string='Dirección Sucursal', required=True, default='')

    city_id = fields.Many2One('res.city', string='comuna sucursal')