from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_compare, float_is_zero
import json
from odoo.tools import date_utils


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

    producer_id = fields.Many2one('res.partner', related='lot_id.producer_id')

    lot_balance = fields.Float('Stock Disponible', related='lot_id.balance')

    @api.multi
    def _compute_total_reserved(self):
        for item in self:
            item.total_reserved = sum(item.lot_id.stock_production_lot_serial_ids.filtered(
                lambda a: (a.reserved_to_production_id and a.reserved_to_production_id.state not in ['done', 'cancel'])
                          or (a.reserved_to_stock_picking_id and
                              a.reserved_to_stock_picking_id.state not in ['done', 'cancel']
                              )
            ).mapped('display_weight'))

    def verify_negative_quant(self):
        quants = self.env['stock.quant'].search([('product_id.tracking','=','lot'),('quantity', '<', 0), ('location_id.usage', '=', 'internal')])
        if quants:
            for quant in quants:
                try:
                    quant.unlink()
                except:
                    query = 'DELETE FROM stock_quant where id = {}'.format(quant.id)
                    cr = self._cr
                    cr.execute(query)

    @api.model
    def _update_reserved_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None,
                                  strict=False):
        try:
            if self.lot_id:
                self.verify_negative_quant()

                self.lot_id.get_and_update(product_id.id)
                return
            else:
                self.lot_id.get_and_update(product_id.id)
                self.verify_negative_quant()

                return super(StockQuant, self)._update_reserved_quantity(product_id, location_id, quantity, lot_id,
                                                                         package_id, owner_id, strict)
        except UserError:
            if product_id.tracking == 'lot':
                self.lot_id.get_and_update(product_id.id)
                self.verify_negative_quant()
                return
            res = super(StockQuant, self)._update_reserved_quantity(product_id, location_id, quantity, lot_id,
                                                                         package_id, owner_id, strict)
            self.verify_negative_quant()
            return res
