from odoo import fields, models, api


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    unpelled_state = fields.Selection([
        ('waiting', 'En Espera'),
        ('drying', 'Secando'),
        ('done', 'Terminado')
    ],
        'Estado',
    )

    product_variety = fields.Char(
        'Variedad',
        compute='_compute_product_variety'
    )

    producer_id = fields.Many2one(
        'res.partner',
        related='stock_picking_id.partner_id'
    )

    reception_guide_number = fields.Integer(
        'Guía',
        related='stock_picking_id.guide_number'
    )

    reception_state = fields.Selection(
        string='Estado de la reecepción',
        related='stock_picking_id.state'
    )

    product_canning = fields.Char(
        'Envase',
        compute='_compute_reception_data'
    )

    is_prd_lot = fields.Boolean('Es Lote de salida de Proceso')

    is_standard_weight = fields.Boolean('Series Peso Estandar')

    standard_weight = fields.Float('Peso Estandar')

    qty_standard_serial = fields.Integer('Cantidad de Series')

    stock_production_lot_serial_ids = fields.One2many(
        'stock.production.lot.serial',
        'stock_production_lot_id',
        string="Detalle"
    )

    stock_production_lot_available_serial_ids = fields.One2many(
        'stock.production.lot.serial',
        compute='_compute_stock_production_lot_available_serial_ids',
        string='Series Disponibles'
    )

    total_serial = fields.Float(
        'Total',
        compute='_compute_total_serial'
    )

    count_serial = fields.Integer(
        'Total Series',
        compute='_compute_count_serial'
    )

    available_total_serial = fields.Float(
        'Total Disponible',
        compute='_compute_available_total_serial',
        search='_search_available_total_serial'
    )

    qty_to_reserve = fields.Float('Cantidad a Reservar')

    is_reserved = fields.Boolean('Esta reservado?', compute='reserved', default=False)

    label_producer_id = fields.Many2one('res.partner','Productor')

    context_picking_id = fields.Integer(
        'picking del contexto',
        compute='_compute_context_picking_id'
    )

    pallet_ids = fields.One2many(
        'manufacturing.pallet',
        compute='_compute_pallet_ids'
    )

    picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='Bodega',
        related='stock_picking_id.picking_type_id'

    )

    reception_net_weight = fields.Float(
        'kg. Neto',
        related='stock_picking_id.net_weight'
    )

    reception_date = fields.Datetime(
        'Fecha Recepción',
        related='stock_picking_id.truck_in_date'
    )

    reception_elapsed_time = fields.Char(
        'Hr Camión en Planta',
        related='stock_picking_id.elapsed_time'
    )

    oven_init_active_time = fields.Integer(
        'Inicio Tiempo Activo',
        related='oven_use_ids.init_active_time'
    )

    finish_active_time = fields.Integer(
        'Fin Tiempo Activo',
        related='oven_use_ids.finish_active_time'
    )

    oven_use_ids = fields.One2many(
        'oven.use',
        'used_lot_id',
        'Uso de Hornos',
        sort='active_seconds desc'
    )

    drier_counter = fields.Integer(
        'Hr en Secador',
        related='oven_use_ids.active_seconds'
    )

    stock_picking_id = fields.Many2one(
        'stock.picking',
        'Recepción'
    )

    @api.multi
    def _compute_count_serial(self):
        for item in self:
            item.count_serial = len(item.stock_production_lot_serial_ids)

    @api.multi
    def _compute_product_variety(self):
        for item in self:
            item.product_variety = item.product_id.get_variety()

    @api.multi
    def _compute_pallet_ids(self):
        for item in self:
            item.pallet_ids = item.stock_production_lot_available_serial_ids.mapped('pallet_id')

    @api.multi
    def _compute_context_picking_id(self):
        for item in self:
            if 'stock_picking_id' in self.env.context:
                item.context_picking_id = self.env.context['stock_picking_id']

    @api.multi
    def _compute_stock_production_lot_available_serial_ids(self):
        for item in self:
            item.stock_production_lot_available_serial_ids = item.stock_production_lot_serial_ids.filtered(
                lambda a: not a.reserved_to_stock_picking_id
            )

    @api.multi
    def _compute_available_total_serial(self):
        for item in self:
            item.available_total_serial = sum(item.stock_production_lot_serial_ids.filtered(
                lambda a: not a.consumed
            ).mapped('display_weight'))

    @api.multi
    def _search_available_total_serial(self, operator, value):
        stock_production_lot_ids = self.env['stock.production.lot.serial'].search([
            ('consumed', '=', False),
            ('reserved_to_stock_picking_id', '=', False)
        ]).mapped('stock_production_lot_id')

        if operator == '>':
            stock_production_lot_ids = stock_production_lot_ids.filtered(
                lambda a: sum(a.stock_production_lot_serial_ids.mapped('display_weight')) > value
            )
        elif operator == '=':
            stock_production_lot_ids = stock_production_lot_ids.filtered(
                lambda a: sum(a.stock_production_lot_serial_ids.mapped('display_weight')) == value
            )
        elif operator == '<':
            stock_production_lot_ids = stock_production_lot_ids.filtered(
                lambda a: sum(a.stock_production_lot_serial_ids.mapped('display_weight')) < value
            )
        elif operator == '>=':
            stock_production_lot_ids = stock_production_lot_ids.filtered(
                lambda a: sum(a.stock_production_lot_serial_ids.mapped('display_weight')) >= value
            )
        elif operator == '<=':
            stock_production_lot_ids = stock_production_lot_ids.filtered(
                lambda a: sum(a.stock_production_lot_serial_ids.mapped('display_weight')) <= value
            )

        return [('id', 'in', stock_production_lot_ids.mapped('id'))]

    @api.multi
    def _compute_reception_data(self):
        for item in self:
            stock_picking = self.env['stock.picking'].search([('name', '=', item.name)])
            if stock_picking:
                item.product_canning = stock_picking[0].get_canning_move().name

    @api.multi
    def _compute_total_serial(self):
        for item in self:
            item.total_serial = sum(item.stock_production_lot_serial_ids.mapped('display_weight'))

    @api.multi
    def add_to_packing_list(self):
        picking_id = None
        if 'stock_picking_id' in self.env.context:
            picking_id = self.env.context['stock_picking_id']
        for item in self:
            serial_to_assign_ids = item.stock_production_lot_serial_ids.filtered(
                lambda a: not a.consumed and not a.reserved_to_stock_picking_id
            )

            serial_to_assign_ids.with_context(stock_picking_id=picking_id).reserve_picking()

    @api.multi
    def reserved(self):
        print('')
        # for item in self:
        #     if item.qty_standard_serial == 0:
        #         if 'stock_picking_id' in self.env.context:
        #             stock_picking_id = self.env.context['stock_picking_id']
        #             reserve = self.env.context['reserved']
        #             models._logger.error(reserve)
        #             stock_picking = self.env['stock.picking'].search([('id', '=', stock_picking_id)])
        #             if stock_picking:
        #                 stock_move = stock_picking.move_ids_without_package.filtered(
        #                     lambda x: x.product_id == item.product_id
        #                 )
        #                 stock_quant = item.get_stock_quant()
        #                 stock_quant.sudo().update({
        #                     'reserved_quantity': stock_quant.reserved_quantity + item.qty_to_reserve
        #                 })
        #                 item.update({
        #                     'qty_to_reserve': reserve,
        #                     'is_reserved': True
        #                 })
        #                 models._logger.error(item.is_reserved)
        #                 item.is_reserved = True
        #                 models._logger.error(item.is_reserved)
        #                 move_line = self.env['stock.move.line'].create({
        #                     'product_id': item.product_id.id,
        #                     'lot_id': item.id,
        #                     'product_uom_qty': reserve,
        #                     'product_uom_id': stock_move.product_uom.id,
        #                     'location_id': stock_quant.location_id.id,
        #                     'location_dest_id': stock_picking.partner_id.property_stock_customer.id
        #                 })
        #                 models._logger.error(item.is_reserved)
        #                 stock_move.sudo().update({
        #                     'move_line_ids': [
        #                         (4, move_line.id)
        #                     ]
        #                 })

    @api.multi
    def unreserved(self):
        for item in self:
            stock_picking = None
            if 'stock_picking_id' in self.env.context:
                stock_picking_id = self.env.context['stock_picking_id']
                stock_picking = self.env['stock.picking'].search([('id', '=', stock_picking_id)])
            if stock_picking:

                item.stock_production_lot_serial_ids.filtered(
                    lambda a: a.reserved_to_stock_picking_id.id == stock_picking_id
                ).unreserved_picking()

                stock_move = stock_picking.move_ids_without_package.filtered(
                    lambda x: x.product_id == item.product_id
                )
                move_line = stock_move.move_line_ids.filtered(
                    lambda a: a.lot_id.id == item.id and a.product_uom_qty == stock_move.reserved_availability
                )
                item.update({
                    'qty_to_reserve': 0,
                    'is_reserved': False
                })

                stock_quant = item.get_stock_quant()

                stock_quant.sudo().update({
                    'reserved_quantity': stock_quant.reserved_quantity - stock_move.product_uom_qty
                })

                for ml in move_line:
                    ml.write({'move_id': None, 'reserved_availability': 0})

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

    def show_available_serial(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.production.lot',
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(self.env.ref('dimabe_manufacturing.available_lot_form_view').id, 'form')],
            'target': 'new',
            'context': self.env.context
        }
