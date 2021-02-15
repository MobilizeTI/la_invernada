from odoo import fields, models, api
from odoo.addons import decimal_precision as dp


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'
    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'el lote que intenta crear, ya existe en el sistema')
    ]

    unpelled_state = fields.Selection([
        ('waiting', 'En Espera'),
        ('drying', 'Secando'),
        ('done', 'Terminado')
    ],
        'Estado',
    )

    can_add_serial = fields.Boolean(
        'Puede Agregar Series',
        compute='_compute_can_add_serial'
    )

    producer_ids = fields.One2many(
        'res.partner',
        compute='_compute_producer_ids'
    )

    product_variety = fields.Char(
        'Variedad',
        compute='_compute_product_variety'
    )

    producer_id = fields.Many2one(
        'res.partner',
        string='Productor'
    )

    reception_guide_number = fields.Integer(
        'Guía',
        related='stock_picking_id.guide_number',
        store=True
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

    is_standard_weight = fields.Boolean(
        'Series Peso Estandar',
        related='product_id.is_standard_weight'
    )

    standard_weight = fields.Float(
        'Peso Estandar',
        related='product_id.weight',
        digits=dp.get_precision('Product Unit of Measure')
    )

    qty_standard_serial = fields.Integer('Cantidad de Series')

    stock_production_lot_serial_ids = fields.One2many(
        'stock.production.lot.serial',
        'stock_production_lot_id',
        string="Detalle"
    )

    serial_without_pallet_ids = fields.One2many(
        'stock.production.lot.serial',
        compute='_compute_serial_without_pallet_ids',
        string='Series sin Pallet'
    )

    stock_production_lot_available_serial_ids = fields.One2many(
        'stock.production.lot.serial',
        'stock_production_lot_id',
        domain=[('reserved_to_stock_picking_id', '=', None), ('consumed', '=', False)],
        string='Series Disponibles'
    )

    total_serial = fields.Float(
        'Total',
        compute='_compute_total_serial',
        digits=dp.get_precision('Product Unit of Measure')
    )

    count_serial = fields.Integer(
        'Total Series',
        compute='_compute_count_serial'
    )

    available_total_serial = fields.Float(
        'Total Disponible',
        compute='_compute_available_total_serial',
        search='_search_available_total_serial',
        digits=dp.get_precision('Product Unit of Measure')
    )

    qty_to_reserve = fields.Float(
        'Cantidad a Reservar',
        digits=dp.get_precision('Product Unit of Measure')
    )

    context_picking_id = fields.Integer(
        'picking del contexto',
        compute='_compute_context_picking_id'
    )

    pallet_ids = fields.One2many(
        'manufacturing.pallet',
        'lot_id'
    )

    picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='Bodega',
        related='stock_picking_id.picking_type_id',
        store=True

    )

    reception_net_weight = fields.Float(
        'kg. Neto',
        related='stock_picking_id.net_weight',
        digits=dp.get_precision('Product Unit of Measure'),
        store=True
    )

    reception_date = fields.Datetime(
        'Fecha Recepción',
        related='stock_picking_id.truck_in_date',
        store=True
    )

    reception_elapsed_time = fields.Char(
        'Hr Camión en Planta',
        related='stock_picking_id.elapsed_time',
        store=True
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

    all_pallet_ids = fields.One2many(
        'manufacturing.pallet',
        'lot_id',
        string='pallets'
    )

    label_durability_id = fields.Many2one(
        'label.durability',
        'Durabilidad Etiqueta'
    )

    is_dried_lot = fields.Boolean(
        'Es lote de Secado'
    )

    product_variety = fields.Char(
        'Variedad del Producto',
        related='product_id.variety',
        store=True
    )

    product_caliber = fields.Char(
        'Calibre del Producto',
        related='product_id.caliber',
        store=True
    )

    harvest = fields.Integer(string='Cosecha', compute='_compute_lot_harvest', store=True)

    dried_report_product_name = fields.Char(compute='_compute_lot_oven_use')

    location_id = fields.Many2one('stock.location', compute='_compute_lot_location')

    serial_not_consumed = fields.Integer('Envases disponible', compute='_compute_serial_not_consumed')

    available_kg = fields.Float('Kilos Disponibles', store=True)

    available_weight = fields.Float('Datos Disponibles')

    show_guide_number = fields.Char('Guia', compute='_compute_guide_number')

    reception_weight = fields.Float('Kilos Recepcionados', compute='_compute_reception_weight')

    sale_order_id = fields.Many2one('sale.order', compute='_compute_sale_order_id', store=True)

    @api.multi
    def test(self):
        for item in self:
            serial_not_consumed = self.env['stock.production.lot.serial'].search(
                [('consumed', '=', False), ('stock_production_lot_id.is_prd_lot', '=', True),
                 ('production_id.state', '=', 'done'), ('reserved_to_stock_picking_id', '!=', None)])
            for lot in serial_not_consumed.mapped('stock_production_lot_id'):
                models._logger.error(
                    f"Lot Product {lot.product_id.display_name} Qty {sum(serial_not_consumed.filtered(lambda x: x.stock_production_lot_id.id == lot.id).mapped('display_weight'))} ")

    @api.depends('stock_production_lot_serial_ids')
    @api.multi
    def _compute_sale_order_id(self):
        for item in self:
            if item.is_prd_lot:
                production_id = item.stock_production_lot_serial_ids.mapped('production_id')
                if production_id:
                    stock_picking_id = production_id.stock_picking_id
                    if stock_picking_id:
                        item.sale_order_id = self.env['sale.order'].search([('name', '=', stock_picking_id.origin)])

    @api.multi
    def _compute_reception_weight(self):
        for item in self:
            if not item.stock_picking_id:
                weight = self.env['stock.picking'].search([('name', '=', item.name)])
                item.reception_weight = weight.production_net_weight
            if item.stock_picking_id:
                item.reception_weight = item.stock_picking_id.production_net_weight
            if item.is_dried_lot:
                dried = self.env['dried.unpelled.history'].search(
                    [('out_lot_id', '=', item.id)]).total_out_weight
                item.reception_weight = dried

    @api.multi
    def check_duplicate(self):
        for item in self:
            if len(item.stock_production_lot_serial_ids) > 999:
                not_duplicates = []
                duplicates = []
                for serial in item.stock_production_lot_serial_ids.mapped('serial_number'):
                    if serial not in not_duplicates:
                        not_duplicates.append(serial)
                    else:
                        duplicates.append(serial)
                serie = len(not_duplicates)

                if len(duplicates) > 1:
                    item.stock_production_lot_serial_ids[999].update({
                        'serial_number': item.name + '1000'
                    })
                    for duplicate in duplicates:
                        serial = self.env['stock.production.lot.serial'].search([('serial_number', '=', duplicate)])
                        serie += 1
                        models._logger.error(serial)
                        if len(serial) > 1:
                            serial[1].write({
                                'serial_number': item.name + '{}'.format(serie)
                            })
                        else:
                            serial.write({
                                'serial_number': item.name + '{}'.format(serie)
                            })

    @api.multi
    def _compute_guide_number(self):
        for item in self:
            if item.stock_picking_id:
                item.show_guide_number = str(item.stock_picking_id.guide_number)
            else:
                reception = self.env['stock.picking'].search([('name', '=', item.name)])
                item.show_guide_number = str(reception.guide_number)
            if item.is_dried_lot:
                dried = self.env['dried.unpelled.history'].search(
                    [('out_lot_id', '=', item.id)])
                item.show_guide_number = dried.lot_guide_numbers

    @api.depends('stock_production_lot_serial_ids')
    @api.multi
    def _compute_lot_harvest(self):
        for item in self:
            if item.stock_production_lot_serial_ids:
                item.harvest = item.stock_production_lot_serial_ids[0].harvest

    @api.multi
    def _compute_lot_location(self):
        for item in self:
            stock_quant = item.get_stock_quant()
            if len(stock_quant) < 1:
                item.location_id = stock_quant.location_id
            else:
                location_id = self.env['stock.picking'].search([('name', '=', item.name)])
                item.location_id = location_id.location_dest_id
            if item.stock_picking_id:
                item.location_id = item.stock_picking_id.location_dest_id
            if item.is_dried_lot:
                location_id_dried = self.env['dried.unpelled.history'].search(
                    [('out_lot_id', '=', item.id)]).dest_location_id
                item.location_id = location_id_dried
            if item.is_prd_lot:
                if item.stock_production_lot_serial_ids.mapped('production_id').state == 'done':
                    item.location_id = item.stock_production_lot_serial_ids.mapped('production_id').location_dest_id

    @api.multi
    def _compute_serial_not_consumed(self):
        for item in self:
            item.serial_not_consumed = len(item.stock_production_lot_serial_ids.filtered(lambda a: not a.consumed))

    @api.multi
    def _compute_can_add_serial(self):
        for item in self:
            if item.is_prd_lot:
                item.can_add_serial = True

    @api.multi
    def _compute_serial_without_pallet_ids(self):
        for item in self:
            if item.product_id.is_standard_weight:
                item.serial_without_pallet_ids = item.stock_production_lot_serial_ids.filtered(
                    lambda a: not a.pallet_id
                )

    @api.onchange('label_durability_id')
    def onchange_label_durability_id(self):
        if self.stock_production_lot_serial_ids:
            for serial_id in self.stock_production_lot_serial_ids:
                serial_id.write({
                    'label_durability_id': self.label_durability_id.id
                })

    @api.multi
    def _compute_count_serial(self):
        for item in self:
            item.count_serial = len(item.stock_production_lot_serial_ids)

    @api.multi
    def print_all_serial(self):
        return self.env.ref('dimabe_manufacturing.action_print_all_serial') \
            .report_action(self.stock_production_lot_serial_ids)

    @api.multi
    def _compute_product_variety(self):
        for item in self:
            item.product_variety = item.product_id.get_variety()

    @api.multi
    def _compute_pallet_ids(self):
        for item in self:
            if item.product_id.is_standard_weight:
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
                lambda a: not a.reserved_to_stock_picking_id
            ).mapped('display_weight'))

    @api.multi
    def _compute_producer_ids(self):

        for item in self:
            if item.is_prd_lot:
                workorder = self.env['mrp.workorder'].search([
                    '|',
                    ('final_lot_id', '=', item.id),
                    ('production_finished_move_line_ids.lot_id', '=', item.id)
                ])

                producers = workorder.mapped('potential_serial_planned_ids.stock_production_lot_id.producer_id')

                item.producer_ids = self.env['res.partner'].search([
                    '|',
                    ('id', 'in', producers.mapped('id')),
                    ('always_to_print', '=', True)
                ])
            elif item.is_dried_lot:
                dried_data = self.env['unpelled.dried'].search([
                    ('out_lot_id', '=', item.id)
                ])
                if not dried_data:
                    dried_data = self.env['dried.unpelled.history'].search([
                        ('out_lot_id', '=', item.id)
                    ])
                if dried_data:
                    item.producer_ids = self.env['res.partner'].search([
                        '|',
                        ('id', '=', dried_data.in_lot_ids.mapped('stock_picking_id.partner_id.id')),
                        ('always_to_print', '=', True)
                    ])

            else:
                item.producer_ids = self.env['res.partner'].search([
                    '|',
                    ('supplier', '=', True),
                    ('always_to_print', '=', True)

                ])
            if item.producer_ids:
                item.producer_ids = item.producer_ids.filtered(
                    lambda a: a.company_type == 'company' or a.always_to_print
                )

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
            if item.stock_picking_id:
                item.product_canning = item.stock_picking_id.get_canning_move().name

    @api.multi
    def _compute_total_serial(self):
        for item in self:
            item.total_serial = sum(item.stock_production_lot_serial_ids.mapped('display_weight'))

    @api.multi
    def add_to_packing_list(self):
        picking_id = None
        if 'stock_picking_id' in self.env.context:
            picking_id = self.env.context['stock_picking_id']
            models._logger.error('Line 533 {}'.format(picking_id))
            stock_picking = self.env['stock.picking'].search([('id', '=', picking_id)])
            models._logger.error('Line 535 {}'.format(stock_picking))
        for item in self:
            serial_to_assign_ids = item.stock_production_lot_serial_ids.filtered(
                lambda a: not a.consumed and not a.reserved_to_stock_picking_id
            )
            models._logger.error('Line 540 {}'.format(serial_to_assign_ids))
            lot_id = serial_to_assign_ids.mapped('stock_production_lot_id')
            models._logger.error('Line 542 {}'.format(lot_id))
            for lot in lot_id:
                available_total_serial = lot.available_total_serial
                models._logger.error(available_total_serial)
                serial_to_assign_ids.update({
                    'reserved_to_stock_picking_id': stock_picking.id
                })
                stock_move = stock_picking.move_lines.filtered(
                    lambda a: a.product_id == item.product_id
                )
                models._logger.error(stock_move)
                stock_quant = item.get_stock_quant()
                models._logger.error(stock_quant)
                if not stock_quant:
                    raise models.ValidationError('El lote {} aún se encuentra en proceso.'.format(
                        item.name
                    ))

                move_line = self.env['stock.move.line'].create({
                    'product_id': lot.product_id.id,
                    'lot_id': lot.id,
                    'qty_done': available_total_serial,
                    'product_uom_id': stock_move.product_uom.id,
                    'location_id': stock_quant.location_id.id,
                    # 'qty_done': item.display_weight,
                    'location_dest_id': stock_picking.partner_id.property_stock_customer.id
                })
                models._logger.error(stock_quant)
                stock_move.sudo().update({
                    'move_line_ids': [
                        (4, move_line.id)
                    ]
                })

                stock_picking.update({
                    'move_line_ids': [
                        (4, move_line.id)
                    ]
                })

                stock_quant.sudo().update({
                    'reserved_quantity': stock_quant.total_reserved
                })
            # serial_to_assign_ids.with_context(stock_picking_id=picking_id).reserve_picking()

    @api.multi
    def unreserved(self):
        for item in self:
            stock_picking = None
            if 'stock_picking_id' in self.env.context:
                stock_picking_id = self.env.context['stock_picking_id']
                stock_picking = self.env['stock.picking'].search([('id', '=', stock_picking_id)])
            if stock_picking:
                quant = self.env['stock.quant'].search(
                    [('lot_id', '=', self.id), ('product_id', '=', self.product_id.id)])
                quant.write({
                    'reserved_quantity': 0,
                    'quantity': sum(self.stock_production_lot_serial_ids.filtered(
                        lambda a: a.reserved_to_stock_picking_id == stock_picking_id).mapped('display_weight'))
                })
                self.pallet_ids.filtered(lambda a: a.reserved_to_stock_picking_id.id == stock_picking_id).write({
                    'reserved_to_stock_picking_id': None
                })
                self.stock_production_lot_serial_ids.filtered(
                    lambda a: a.reserved_to_stock_picking_id.id == stock_picking_id and not a.consumed).write({
                    'reserved_to_stock_picking_id': None
                })
                stock_picking.move_line_ids_without_package.filtered(lambda a: a.lot_id.id == self.id).write({
                    'product_uom_qty': sum(stock_picking.packing_list_ids.mapped('display_weight'))
                })

    @api.multi
    def write(self, values):
        for item in self:
            res = super(StockProductionLot, self).write(values)
            if not item.product_id.is_standard_weight:
                for serial in item.stock_production_lot_serial_ids:
                    if not serial.serial_number:
                        if len(item.stock_production_lot_serial_ids) > 1:
                            item.stock_production_lot_serial_ids[0].write({
                                'serial_number': item.name + '001'
                            })
                            counter = int(item.stock_production_lot_serial_ids.filtered(lambda a: a.serial_number)[
                                              -1].serial_number) + 1
                        else:
                            counter = 1
                        tmp = '00{}'.format(counter)
                        serial.serial_number = item.name + tmp[-3:]
                        item.write({
                            'available_kg': sum(
                                item.stock_production_lot_serial_ids.filtered(lambda a: not a.consumed).mapped(
                                    'real_weight'))
                        })
            else:
                if len(item.stock_production_lot_serial_ids) > 999:
                    item.check_duplicate()
            return res

    @api.multi
    def generate_standard_pallet(self):
        for item in self:

            if not item.producer_id:
                raise models.ValidationError('debe seleccionar un productor')
            if not self.env['mrp.workorder'].search([('final_lot_id', '=', item.id)]):
                pallet = self.env['manufacturing.pallet'].create({
                    'producer_id': item.producer_id.id,
                    'sale_order_id': self.env['mrp.workorder'].search([('final_lot_id', '=', item.id)]).sale_order_id,
                    'lot_id': self.id
                })
            else:
                pallet = self.env['manufacturing.pallet'].create({
                    'producer_id': item.producer_id.id,
                    'lot_id': self.id
                })

            for counter in range(item.qty_standard_serial):
                tmp = '00{}'.format(1 + len(item.stock_production_lot_serial_ids))

                item.env['stock.production.lot.serial'].create({
                    'stock_production_lot_id': item.id,
                    'display_weight': item.product_id.weight,
                    'serial_number': item.name + tmp[-3:],
                    'belongs_to_prd_lot': True,
                    'pallet_id': pallet.id,
                    'producer_id': pallet.producer_id.id
                })
            pallet.update({
                'state': 'close'
            })

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

    @api.multi
    def add_selection(self):
        picking_id = int(self.env.context['dispatch_id'])
        if not self.stock_production_lot_serial_ids.filtered(lambda a: a.to_add) and not self.pallet_ids.filtered(
                lambda a: a.add_picking):
            raise models.UserError('No se a seleccionado nada')
        if self.pallet_ids.filtered(lambda a: a.add_picking):
            self.add_selection_pallet(picking_id)
        if self.stock_production_lot_serial_ids.filtered(lambda a: a.to_add):
            self.add_selection_serial(picking_id)
        picking = self.env['stock.picking'].search([('id', '=', picking_id)])
        if not picking.mapped('move_line_ids_without_package').filtered(
                lambda a: a.product_id.id == self.product_id.id and a.lot_id.id == self.id):
            self.env['stock.move.line'].create({
                'move_id': picking.move_ids_without_package.filtered(
                    lambda a: a.product_id.id == self.product_id.id).id,
                'product_id': self.product_id.id,
                'lot_id': self.id,
                'product_uom_id': self.product_id.uom_id.id,
                'product_uom_qty': sum(self.stock_production_lot_serial_ids.filtered(
                    lambda a: a.reserved_to_stock_picking_id.id == picking_id).mapped('display_weight')),
                'picking_id': picking_id,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.partner_id.property_stock_customer.id
            })
        else:
            move_line = picking.mapped('move_line_ids_without_package').filtered(
                lambda a: a.product_id.id == self.product_id.id and a.lot_id.id == self.id)
            move_line.write({
                'product_uom_qty': sum(self.stock_production_lot_serial_ids.filtered(
                    lambda a: a.reserved_to_stock_picking_id.id == picking_id).mapped('display_weight'))
            })

    def add_selection_serial(self, picking_id):
        weight = sum(
            self.stock_production_lot_serial_ids.filtered(
                lambda a: a.reserved_to_stock_picking_id == picking_id).mapped(
                'display_weight'))
        quant = self.env['stock.quant'].search([('lot_id', '=', self.id), ('location_id.usage', '=', 'internal')])
        picking = self.env['stock.picking'].sudo().search([('id', '=', picking_id)])
        pallets = self.stock_production_lot_serial_ids.filtered(lambda a: a.to_add).mapped('pallet_id')
        for pallet in pallets:
            pallet.write({
                'reserved_to_stock_picking_id': picking_id
            })
        self.stock_production_lot_serial_ids.filtered(lambda a: a.to_add).write({
            'reserved_to_stock_picking_id': picking_id
        })
        quant.write({
            'reserved_quantity': sum(self.stock_production_lot_serial_ids.filtered(
                lambda a: a.reserved_to_stock_picking_id).mapped('display_weight')),
            'quantity': sum(self.stock_production_lot_serial_ids.filtered(
                lambda a: not a.reserved_to_stock_picking_id).mapped('display_weight'))
        })
        dispatch_line = picking.dispatch_line_ids.filtered(
            lambda a: a.product_id.id == self.product_id.id and self.sale_order_id.id == a.sale_id.id)
        dispatch_line.write({
            'real_dispatch_qty': dispatch_line.real_dispatch_qty + weight
        })
        self.stock_production_lot_serial_ids.filtered(lambda a: a.to_add).write({
            'to_add': False
        })

    def add_selection_pallet(self, picking_id):
        quant = self.env['stock.quant'].search([('lot_id', '=', self.id), ('location_id.usage', '=', 'internal')])
        picking = self.env['stock.picking'].sudo().search([('id', '=', picking_id)])
        self.pallet_ids.filtered(lambda a: a.add_picking).write({
            'reserved_to_stock_picking_id': picking_id
        })
        weight = sum(
            self.pallet_ids.filtered(lambda a: a.reserved_to_stock_picking_id == picking_id).mapped(
                'lot_serial_ids').filtered(lambda a: not a.reserved_to_stock_picking_id).mapped(
                'display_weight')
        )
        quant.write({
            'reserved_quantity': quant.reserved_quantity + weight,
            'quantity': quant.quantity - weight
        })
        dispatch_line = picking.dispatch_line_ids.filtered(
            lambda a: a.product_id.id == self.product_id.id and self.sale_order_id.id == a.sale_id.id)
        dispatch_line.write({
            'real_dispatch_qty': dispatch_line.real_dispatch_qty + sum(
                self.pallet_ids.filtered(lambda a: a.add_picking).mapped('lot_serial_ids').mapped('display_weight'))
        })
        for pallet in self.pallet_ids.filtered(lambda a: a.add_picking):
            pallet.lot_serial_ids.filtered(lambda a: not a.reserved_to_stock_picking_id).write({
                'reserved_to_stock_picking_id': picking_id
            })
        self.pallet_ids.filtered(lambda a: a.add_picking).write({
            'add_picking': False
        })
