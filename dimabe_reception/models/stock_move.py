from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    has_serial_generated = fields.Boolean(
        'tiene series generadas'
    )

    is_mp = fields.Boolean(
        'es mp',
        related='product_id.categ_id.is_mp'
    )

    product_id = fields.Many2one(
        'product.product',
        'Product',
        domain=lambda self: self._domain_filter(),
        index=True,
        required=True,
        states={'done': [('readonly', True)]}
    )

    products_can_be_stored = fields.Many2many(
        'product.category',
        'productos que pueden ser almacenados',
        related='picking_type_id.warehouse_id.products_can_be_stored'
    )

    def _domain_filter(self):
        domain = [
            ('type', 'in', ['product', 'consu']),
            # ('categ_id', 'in', self.picking_type_id.warehouse_id.products_can_be_stored)
        ]
        return domain

    @api.multi
    def write(self, values):
        res = super(StockMove, self).write(values)

        for stock_move in self:

            if stock_move.picking_id and stock_move.picking_id.picking_type_code == 'incoming':
                if stock_move.product_id.tracking == 'lot' and not stock_move.has_serial_generated:
                    for stock_move_line in stock_move.move_line_ids:
                        if stock_move.product_id.categ_id.is_mp:
                            total_qty = stock_move.picking_id.get_canning_move().product_uom_qty

                            calculated_weight = stock_move_line.qty_done / total_qty
                            if stock_move_line.lot_id:

                                for i in range(int(total_qty)):
                                    tmp = '00{}'.format(i + 1)
                                    self.env['stock.production.lot.serial'].create({
                                        'calculated_weight': calculated_weight,
                                        'stock_production_lot_id': stock_move_line.lot_id.id,
                                        'serial_number': '{}{}'.format(stock_move_line.lot_name, tmp[-3:])
                                    })

                                stock_move.has_serial_generated = True
        return res
