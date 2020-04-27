from odoo import fields, models, api
from odoo.addons import decimal_precision as dp


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    total_reserved = fields.Float(
        'Total Reservado',
        compute='_compute_total_reserved',
        digits=dp.get_precision('Product Unit of Measure')
    )

    product_variety = fields.Char(
        'Variedad del Producto',
        related='product_id.variety'
    )

    product_caliber = fields.Char(
        'Calibre del Producto',
        related='product_id.caliber'
    )

    reception_guide_number = fields.Integer(
        'Guía',
        related='lot_id.stock_picking_id.guide_number',
        store=True
    )

    producer_id = fields.Many2one('res.partner',related='lot_id.producer_id')

    lot_balance = fields.Float('Stock Disponible',related='lot_id.balance')

    is_mp = fields.Boolean('Es Materia Prima')

    @api.multi
    def _compute_is_mp(self):
        for item in self:
            item.is_mp = 'Materia Prima' in item.product_id.categ_id.name
            models._logger.error(item.is_mp)

    @api.multi
    def _compute_total_reserved(self):
        for item in self:
            item.total_reserved = sum(item.lot_id.stock_production_lot_serial_ids.filtered(
                lambda a: (a.reserved_to_production_id and a.reserved_to_production_id.state not in ['done', 'cancel'])
                          or (a.reserved_to_stock_picking_id and
                              a.reserved_to_stock_picking_id.state not in ['done', 'cancel']
                              )
            ).mapped('display_weight'))
