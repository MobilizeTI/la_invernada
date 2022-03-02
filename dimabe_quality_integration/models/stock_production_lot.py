from odoo import fields, models, api
from odoo.addons import decimal_precision as dp


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    quality_analysis_id = fields.Many2one('quality.analysis', 'Análisis de Calidad')

    balance = fields.Float(
        'Stock Disponible',
        digits=dp.get_precision('Product Unit of Measure'),
        compute='_compute_balance',
        search='_search_balance'
    )

    @api.multi
    def _compute_balance(self):
        for item in self:
            quant = self.env['stock.quant'].sudo().search([('lot_id.id','=',item.id),('location_id.usage','=','internal')],limit=1)
            if quant:
                item.balance = quant.quantity
            elif item.get_stock_quant():
                item.balance = item.get_stock_quant()[0].balance
            else:
                item.balance = 0

    def _search_balance(self, operator, value):
        lot_ids = self.env['stock.quant'].search([
            ('balance', operator, value),
            ('location_id.name', '=', 'Stock')
        ]).mapped('lot_id')
        return [('id', 'in', lot_ids.mapped('id'))]
