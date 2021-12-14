# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, exceptions, SUPERUSER_ID


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'
    
    company_dest_id = fields.Many2one('res.company', 'Compañía Destino', help='Valor por defecto para las operaciones')