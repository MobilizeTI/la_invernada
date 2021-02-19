from odoo import models, fields, api


class ConfirmOrderForReserved(models.TransientModel):
    _name = 'confirm.order.reserved'

    sale_ids = fields.Many2many('sale.order')

    sale_id = fields.Many2one('sale.order', 'Order')

    picking_id = fields.Many2one('stock.picking', 'Picking')

    picking_principal_id = fields.Many2one('stock.picking')

    lot_id = fields.Many2one('stock.production.lot', 'Lote')

    @api.one
    def reserved(self, no_reserved=True):
        if self.lot_id.pallet_ids.filtered(lambda a: a.add_picking):
            self.lot_id.add_selection_pallet(self.picking_principal_id.id)
        if self.lot_id.stock_production_lot_serial_ids.filtered(lambda a: a.to_add):
            self.lot_id.add_selection_serial(self.picking_principal_id.id)
        line = self.picking_principal_id.dispatch_line_ids.filtered(
            lambda a: a.dispatch_id.id == self.picking_id.id and self.sale_id.id)
        line.filtered(lambda a: a.dispatch_id.id == self.picking_id.id).write({
            'real_dispatch_qty': sum(self.lot_id.stock_production_lot_serial_ids.filtered(
                lambda a: a.reserved_to_stock_picking_id.id == self.picking_principal_id.id).mapped('display_weight'))
        })

    @api.one
    def cancel(self):
        raise models.ValidationError('Prueba Cancelar')
