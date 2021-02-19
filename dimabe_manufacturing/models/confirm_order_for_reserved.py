from odoo import models,fields,api


class ConfirmOrderForReserved(models.TransientModel):
    _name ='confirm.order.reserved'

    sale_ids = fields.Many2many('sale.order')

    sale_id = fields.Many2one('sale.order','Order')

    picking_id = fields.Many2one('stock.picking','Picking')

    lot_id = fields.Many2one('stock.production.lot','Lote')

    @api.one
    def reserved(self,no_reserved=True):
        pallet = self.lot_id.pallet_ids.filtered(lambda a: a.add_picking)
        raise models.UserError(pallet)

    @api.one
    def cancel(self):
        raise models.ValidationError('Prueba Cancelar')