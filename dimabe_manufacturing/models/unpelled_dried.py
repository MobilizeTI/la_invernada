from odoo import fields, models, api


class UnpelledDried(models.Model):
    _name = 'unpelled.dried'
    _description = 'clase que para producción de secado y despelonado'

    active = fields.Boolean(
        'Activo',
        default=True
    )

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('progress', 'En Proceso'),
        ('done', 'Terminado'),
        ('cancel', 'Cancelado')
    ],
        'Estado'
    )

    origin_location_id = fields.Many2one(
        'stock.location',
        'Origen del Movimiento'
    )

    dest_location_id = fields.Many2one(
        'stock.location',
        'Destino de Procesados'
    )

    name = fields.Char(
        'Proceso',
        compute='_compute_name'
    )

    producer_id = fields.Many2one(
        'res.partner',
        'Productor',
        domain=[('supplier', '=', True)]
    )

    product_in_id = fields.Many2one(
        'product.product',
        'Producto a ingresar',
        domain=[('categ_id.name', 'ilike', 'verde')]
    )

    in_lot_ids = fields.Many2many(
        'stock.production.lot',
        compute='_compute_in_lot_ids',
        string='Lotes de Entrada'
    )

    in_variety = fields.Char(
        'Variedad Entrante',
        related='product_in_id.variety'
    )

    out_lot_id = fields.Many2one(
        'stock.production.lot',
        'Lote Producción'
    )

    out_serial_ids = fields.One2many(
        'stock.production.lot.serial',
        compute='_compute_out_serial_ids',
        inverse='_inverse_out_serial_ids',
        string='Series de Salida'
    )

    out_product_id = fields.Many2one(
        'product.product',
        'Producto de Salida',
        required=True
    )

    oven_use_ids = fields.One2many(
        'oven.use',
        'unpelled_dried_id',
        'Hornos'
    )

    total_in_weight = fields.Float(
        'Total Ingresado',
        compute='_compute_total_in_weight'
    )

    total_out_weight = fields.Float(
        'Total Secaco',
        compute='_compute_total_out_weight'
    )

    performance = fields.Float(
        'Rendimiento',
        compute='_compute_performance'
    )

    history_ids = fields.One2many(
        'dried.unpelled.history',
        'unpelled_dried_id',
        'Historial'
    )

    @api.multi
    def _compute_performance(self):
        for item in self:
            if item.total_in_weight > 0 and item.total_out_weight > 0:
                item.performance = (item.total_out_weight / item.total_in_weight) * 100

    @api.multi
    def _compute_total_out_weight(self):
        for item in self:
            item.total_out_weight = sum(item.out_serial_ids.mapped('display_weight'))

    @api.multi
    def _compute_total_in_weight(self):
        for item in self:
            item.total_in_weight = sum(item.oven_use_ids.filtered(
                lambda a: a.finish_date
            ).mapped('used_lot_ids').mapped('balance'))

    @api.multi
    def _compute_in_lot_ids(self):
        for item in self:
            item.in_lot_ids = item.oven_use_ids.mapped('used_lot_ids')

    @api.onchange('producer_id')
    def onchange_producer_id(self):
        if self.producer_id not in self.in_lot_ids.mapped('producer_id'):
            for oven_use_id in self.oven_use_ids:
                oven_use_id.used_lot_ids = [(5,)]

    @api.onchange('product_in_id')
    def onchange_product_in_id(self):
        if self.in_variety != self.out_product_id.get_variety():
            self.out_product_id = [(5,)]

    @api.multi
    def _compute_out_serial_ids(self):
        for item in self:
            item.out_serial_ids = item.out_lot_id.stock_production_lot_serial_ids

    @api.multi
    def _inverse_out_serial_ids(self):
        for item in self:
            item.out_lot_id.stock_production_lot_serial_ids = item.out_serial_ids

    @api.multi
    def _compute_name(self):
        for item in self:
            item.name = '{} {}'.format(item.producer_id.name, item.out_lot_id.product_id.display_name)

    @api.model
    def create_out_lot(self):
        name = self.env['ir.sequence'].next_by_code('unpelled.dried')

        out_lot_id = self.env['stock.production.lot'].create({
            'name': name,
            'product_id': self.out_product_id.id,
            'is_prd_lot': True  # probar si funciona bien, de lo contrario dejar en False
        })

        self.write({
            'out_lot_id': out_lot_id.id
        })

    @api.model
    def create_history(self):
        history_id = self.env['dried.unpelled.history'].create({
            'unpelled_dried_id': self.id
        })

        for oven_use_id in self.oven_use_ids.filtered(lambda a: a.finish_date):
            oven_use_id.write({
                'history_id': history_id.id,
                'unpelled_dried_id': None
            })

    @api.model
    def create(self, values_list):
        res = super(UnpelledDried, self).create(values_list)

        res.state = 'draft'

        res.create_out_lot()

        return res

    @api.multi
    def unlink(self):
        for item in self:
            item.oven_use_ids.mapped('dried_oven_id').write({
                'is_in_use': False
            })

        return super(UnpelledDried, self).unlink()

    @api.multi
    def cancel_unpelled_dried(self):
        for item in self:
            item.state = 'cancel'
            item.oven_use_ids.mapped('dried_oven_id').set_is_in_use(False)

    @api.multi
    def finish_unpelled_dried(self):
        for item in self:
            if not item.out_serial_ids:
                raise models.ValidationError('Debe agregar al menos una serie de salida al proceso')

            oven_use_to_close_ids = item.oven_use_ids.filtered(
                lambda a: a.finish_date
            )

            if not oven_use_to_close_ids:
                raise models.ValidationError('no hay hornos terminados que procesar')

            stock_move = self.env['stock.move'].create({
                'name': item.out_lot_id.name,
                'company_id': self.env.user.company_id.id,
                'location_id': item.origin_location_id.id,
                'location_dest_id': item.dest_location_id.id,
                'product_id': item.out_product_id.id,
                'product_uom': item.out_product_id.uom_id.id,
                'product_uom_qty': item.total_out_weight,
                'quantity_done': item.total_out_weight,
                'state': 'done',
            })

            consumed = []

            for used_lot_id in oven_use_to_close_ids.mapped('used_lot_ids'):
                if used_lot_id.get_stock_quant().balance > 0:
                    consumed.append([0, 0, {
                        'lot_name': used_lot_id.name,
                        'reference': used_lot_id.name,
                        'product_id': used_lot_id.product_id.id,
                        'location_id': used_lot_id.get_stock_quant().location_id.id,
                        'location_dest_id': item.origin_location_id.id,
                        'qty_done': used_lot_id.get_stock_quant().balance,
                        'product_uom_qty': 0,
                        'product_uom_id': used_lot_id.product_id.uom_id.id,
                        'lot_id': used_lot_id.id,
                        'state': 'done',
                        'move_id': stock_move.id
                    }])

            prd_move_line = self.env['stock.move.line'].create({
                'lot_name': item.out_lot_id.name,
                'consume_line_ids': consumed,
                'reference': item.out_lot_id.name,
                'product_id': item.out_product_id.id,
                'location_id': item.origin_location_id.id,
                'location_dest_id': item.dest_location_id.id,
                'qty_done': item.total_out_weight,
                'product_uom_qty': 0,
                'product_uom_id': item.out_product_id.uom_id.id,
                'lot_id': item.out_lot_id.id,
                'state': 'done',
                'move_id': stock_move.id
            })

            oven_use_to_close_ids.mapped('dried_oven_id').set_is_in_use(False)

            item.create_history()
            item.create_out_lot()

            if not item.oven_use_ids:
                item.state = 'draft'

    @api.multi
    def go_history(self):
        raise models.ValidationError(self.env.context['unpelled_dried_id'])
