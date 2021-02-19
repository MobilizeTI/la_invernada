from odoo import models, fields, api
from datetime import date

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
        quant = self.env['stock.quant'].search([('lot_id', '=', self.id), ('location_id.usage', '=', 'internal')])
        quant.write({
            'reserved_quantity': sum(self.lot_id.stock_production_lot_serial_ids.filtered(lambda
                                                                                       x: x.reserved_to_stock_picking_id and x.reserved_to_stock_picking_id.state != 'done' and not x.consumed).mapped(
                'display_weight')),
            'quantity': sum(self.lot_id.stock_production_lot_serial_ids.filtered(
                lambda x: not x.reserved_to_stock_picking_id and not x.consumed).mapped('display_weight'))
        })
        self.env['stock.move.line'].create({
            'move_id': self.picking_principal_id.move_ids_without_package.filtered(
                lambda a: a.product_id.id == self.lot_id.product_id.id).id,
            'picking_id': self.picking_principal_id.id,
            'product_id': self.lot_id.product_id.id,
            'product_uom_qty': line.real_dispatch_qty,
            'sale_order_id':self.sale_id.id,
            'lot_id': self.lot_id.id,
            'product_uom_id': self.lot_id.product_id.uom_id.id,
            'location_id': self.picking_principal_id.location_id.id,
            'location_dest_id': self.picking_principal_id.partner_id.property_stock_customer.id,
            'date': date.today()
        })

    @api.one
    def cancel(self):
        raise models.ValidationError('Prueba Cancelar')
