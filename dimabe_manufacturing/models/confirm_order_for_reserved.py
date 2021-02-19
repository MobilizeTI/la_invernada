from odoo import models,fields,api


class ConfirmOrderForReserved(models.TransientModel):
    _name ='confirm.order.reserved'

    sale_ids = fields.Many2many('sale.order','Ordenes para filtro')

    sale_id = fields.Many2one('sale.order','Order')

    picking_id = fields.Many2one('stock.picking','Picking')

    lot_id = fields.Many2one('stock.production.lot','Lote')

    @api.one
    def _reserved(self,no_reserved=True):
        raise models.ValidationError('Prueba')

    @api.one
    def _cancel(self):
        raise models.ValidationError('Prueba Cancelar')