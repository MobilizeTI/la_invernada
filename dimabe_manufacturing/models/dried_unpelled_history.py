from odoo import fields, models, api


class DriedUnpelledHistory(models.Model):
    _name = 'dried.unpelled.history'
    _description = 'Historial de lotes terminados'

    oven_use_ids = fields.One2many(
        'oven.use',
        'history_id',
        'Hornos',
        readonly=True
    )

    unpelled_dried_id = fields.Many2one(
        'unpelled.dried',
        'Proceso de Secado',
        readonly=True,
        required=True,
    )

    producer_id = fields.Many2one(
        'res.partner',
        'Productor',
        readonly=True
    )

    in_product_id = fields.Many2one(
        'product.product',
        'Producto a Ingresar',
        readonly=True
    )

    out_product_id = fields.Many2one(
        'product.product',
        'Producto de Salida',
        readonly=True
    )

    out_lot_id = fields.Many2one(
        'stock.production.lot',
        'Lote de Salida',
        readonly=True
    )

    out_serial_ids = fields.One2many(
        'stock.production.lot.serial',
        related='out_lot_id.stock_production_lot_serial_ids',
        string='Series de Salida'
    )

    total_in_weight = fields.Float(
        'Total Ingresado',
        readonly=True
    )

    total_out_weight = fields.Float(
        'Total Secado',
        readonly=True
    )

    performance = fields.Float(
        'Rendimiento',
        compute='_compute_performance',
        store=True
    )

    origin_location_id = fields.Many2one(
        'stock.location',
        'Origen del Movimiento',
        readonly=True
    )

    dest_location_id = fields.Many2one(
        'stock.location',
        'Destino de Procesados',
        readonly=True
    )

    @api.multi
    def _compute_performance(self):
        for item in self:
            if item.total_in_weight > 0 and item.total_out_weight > 0:
                item.performance = (item.total_out_weight / item.total_in_weight) * 100

    @api.model
    def create(self, values_list):
        res = super(DriedUnpelledHistory, self).create(values_list)
        if 'unpelled_dried_id' in values_list:
            unpelled_dried_id = self.env['unpelled.dried'].search([('id', '=', values_list['unpelled_dried_id'])])

            if unpelled_dried_id:
                res.producer_id = unpelled_dried_id.producer_id.id
                res.in_product_id = unpelled_dried_id.product_in_id.id
                res.out_product_id = unpelled_dried_id.out_product_id.id
                res.out_lot_id = unpelled_dried_id.out_lot_id
                res.oven_use_ids = unpelled_dried_id.oven_use_ids.filtered(
                    lambda a: a.finish_date
                )
                res.total_in_weight = unpelled_dried_id.total_in_weight
                res.total_out_weight = unpelled_dried_id.total_out_weight
                res.origin_location_id = unpelled_dried_id.origin_location_id.id
                res.dest_location_id = unpelled_dried_id.dest_location_id.id
        return res
