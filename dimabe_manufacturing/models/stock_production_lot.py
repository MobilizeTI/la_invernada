from odoo import fields, models, api


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    is_prd_lot = fields.Boolean('Es Lote de salida de Proceso')

    is_standard_weight = fields.Boolean('Series Peso Estandar')

    standard_weight = fields.Float('Peso Estandar')

    qty_standard_serial = fields.Integer('Cantidad de Series')

    stock_production_lot_serial_ids = fields.One2many(
        'stock.production.lot.serial',
        'stock_production_lot_id',
        string="Detalle"
    )

    total_serial = fields.Float(
        'Total',
        compute='_compute_total_serial'
    )

    qty_to_reserve = fields.Float('Cantidad a Reservar')

    @api.multi
    def _compute_total_serial(self):
        for item in self:
            item.total_serial = sum(item.stock_production_lot_serial_ids.mapped('display_weight'))

    @api.multi
    def reserved(self):
        for item in self:
            if item.qty_standard_serial == 0:
                if 'stock_picking_id' in self.env.context:
                    stock_picking_id = self.env.context['stock_picking_id']
                    stock_picking = self.env['stock.picking'].search([('id', '=', stock_picking_id)])
                    if stock_picking:
                        for stock in stock_picking.move_ids_without_package:
                            models._logger.error(item.product_qty -stock.product_uom_qty)



    @api.multi
    def write(self, values):
        for item in self:
            res = super(StockProductionLot, self).write(values)
            counter = 0
            if not item.is_standard_weight:
                for serial in item.stock_production_lot_serial_ids:
                    counter += 1
                    tmp = '00{}'.format(counter)
                    serial.serial_number = item.name + tmp[-3:]
            return res

    @api.multi
    def generate_standard_serial(self):
        for item in self:
            serial_ids = []
            for counter in range(item.qty_standard_serial):
                tmp = '00{}'.format(counter + 1)
                serial = item.stock_production_lot_serial_ids.filtered(
                    lambda a: a.serial_number == item.name + tmp[-3:]
                )
                if serial:
                    if not serial.consumed:
                        serial.update({
                            'display_weight': item.standard_weight
                        })
                        serial_ids.append(serial.id)
                else:
                    new_serial = item.env['stock.production.lot.serial'].create({
                        'stock_production_lot_id': item.id,
                        'display_weight': item.standard_weight,
                        'serial_number': item.name + tmp[-3:],
                        'belong_to_prd_lot': True
                    })
                    serial_ids.append(new_serial.id)
            serial_ids += list(item.stock_production_lot_serial_ids.filtered(
                lambda a: a.consumed
            ).mapped('id'))

            item.stock_production_lot_serial_ids = [(6, 0, serial_ids)]

    @api.model
    def get_stock_quant(self):
        return self.quant_ids.filtered(
            lambda a: a.location_id.name == 'Stock'
        )
