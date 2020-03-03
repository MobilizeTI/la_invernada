from odoo import fields, models, api


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    quality_analysis_id = fields.Many2one('quality.analysis', 'Análisis de Calidad')

    balance = fields.Float('Stock Disponible')
