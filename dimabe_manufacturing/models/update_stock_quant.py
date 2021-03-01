from odoo import models,fields,api

class UpdateStockQuant(models.TransientModel):
    _name = 'update.stock.quant'

    lot_id = field.Many2one('stock.production.lot','Lote')

    @api.multi
    def update(self):


