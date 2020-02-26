from odoo import fields, models, api


class PotentialLot(models.Model):
    _name = 'potential.lot'
    _description = 'posibles lotes para planificación de producción'

    name = fields.Char('lote', related='stock_production_lot_id.name')

    lot_product_id = fields.Many2one(
        'product.product',
        related='stock_production_lot_id.product_id'
    )

    lot_balance = fields.Float(
        related='stock_production_lot_id.balance'
    )

    stock_production_lot_id = fields.Many2one('stock.production.lot', 'lote potencial')

    potential_serial_ids = fields.One2many(
        'stock.production.lot.serial',
        compute='_compute_potential_serial_ids',
    )

    mrp_production_id = fields.Many2one('mrp.production', 'Producción')

    mrp_production_state = fields.Selection(
        string='estado',
        related='mrp_production_id.state'
    )

    qty_to_reserve = fields.Float('Cantidad Reservada')

    is_reserved = fields.Boolean('Reservado')

    @api.multi
    def _compute_potential_serial_ids(self):
        for item in self:
            item.potential_serial_ids = item.stock_production_lot_id.stock_production_lot_serial_ids.filtered(
                lambda a: a.consumed is False and (a.reserved_to_production_id == item.mrp_production_id or not a.reserved_to_production_id)
            )

    @api.model
    def get_stock_quant(self):
        return self.stock_production_lot_id.quant_ids.filtered(
            lambda a: a.location_id.name == 'Stock'
        )

    @api.model
    def get_production_quant(self):
        return self.stock_production_lot_id.quant_ids.filtered(
            lambda a: a.location_id.name == 'Production'
        )

    @api.model
    def get_total_reserved(self):
        return sum(
            self.potential_serial_ids.filtered(
                lambda a: a.reserved_to_production_id == self.mrp_production_id
            ).mapped('display_weight')
        )

    @api.multi
    def reserve_stock(self):
        for item in self:
            serial_to_reserve = item.potential_serial_ids.filtered(lambda a: not a.reserved_to_production_id)

            serial_to_reserve.with_context(mrp_production_id=item.mrp_production_id.id).reserve_serial()

            item.qty_to_reserve = item.get_total_reserved()

            item.is_reserved = True

    @api.multi
    def confirm_reserve(self):
        for item in self:
            item.update({
                'qty_to_reserve': item.get_total_reserved(),
            })

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.multi
    def unreserved_stock(self):
        for item in self:
            serial_to_reserve = item.potential_serial_ids.filtered(
                lambda a: a.reserved_to_production_id == item.mrp_production_id
            )

            serial_to_reserve.unreserved_serial()

            item.qty_to_reserve = 0

            item.is_reserved = False
