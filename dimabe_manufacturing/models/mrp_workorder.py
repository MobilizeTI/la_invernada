from odoo import fields, models, api
from odoo.addons import decimal_precision as dp


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    show_manual_input = fields.Boolean(
        'Digitar Serie Manualmente'
    )

    positioning_state = fields.Selection(
        related='production_id.positioning_state',
        string='Estado movimiento de bodega a producción'
    )

    client_id = fields.Many2one(
        'res.partner',
        related='production_id.client_id',
        string='Cliente'
    )

    destiny_country_id = fields.Many2one(
        'res.country',
        related='production_id.destiny_country_id',
        string='País'
    )

    sale_order_id = fields.Many2one(
        'sale.order',
        related='production_id.stock_picking_id.sale_id',
        string='Pedido de Venta'
    )

    pt_balance = fields.Float(
        'Saldo Bodega PT',
        digits=dp.get_precision('Product Unit of Measure'),
        related='production_id.pt_balance'
    )

    charging_mode = fields.Selection(
        related='production_id.charging_mode',
        string='Modo de Carga'
    )

    client_label = fields.Boolean(
        'Etiqueta Cliente',
        related='production_id.client_label'
    )

    unevenness_percent = fields.Float(
        '% Descalibre',
        digits=dp.get_precision('Product Unit of Measure'),
        related='production_id.unevenness_percent'
    )

    etd = fields.Date(
        'Fecha de Despacho',
        related='production_id.etd'
    )

    label_durability_id = fields.Many2one(
        'label.durability',
        string='Durabilidad Etiqueta',
        related='production_id.label_durability_id'
    )

    observation = fields.Text(
        'Observación',
        related='production_id.observation'
    )

    production_finished_move_line_ids = fields.One2many(
        string='Productos Finalizados',
        related='production_id.finished_move_line_ids'
    )

    summary_out_serial_ids = fields.One2many(
        'stock.production.lot.serial',
        compute='_compute_summary_out_serial_ids',
        string='Resumen de Salidas'
    )

    material_product_ids = fields.One2many(
        'product.product',
        compute='_compute_material_product_ids'
    )

    byproduct_move_line_ids = fields.One2many(
        'stock.move.line',
        compute='_compute_byproduct_move_line_ids',
        string='subproductos'
    )

    potential_serial_planned_ids = fields.One2many(
        'stock.production.lot.serial',
        compute='_compute_potential_lot_planned_ids',
        inverse='_inverse_potential_lot_planned_ids'
    )

    confirmed_serial = fields.Char('Codigo de Barra')

    manufacturing_pallet_ids = fields.One2many(
        'manufacturing.pallet',
        compute='_compute_manufacturing_pallet_ids',
        string='Pallets'
    )

    there_is_serial_without_pallet = fields.Boolean(
        'Hay Series sin pallet',
        compute='_compute_there_is_serial_without_pallet'
    )

    is_match = fields.Boolean('Es Partido', compute='compute_is_match')

    product_variety = fields.Char(related='product_id.variety')

    location_id = fields.Many2one('stock.location', related='production_id.location_dest_id')

    product_qty = fields.Float(related='production_id.product_qty')

    @api.multi
    def compute_is_match(self):
        for item in self:
            item.is_match = item.production_id.routing_id.code == 'RO/00006'

    @api.multi
    def _compute_there_is_serial_without_pallet(self):
        for item in self:
            item.there_is_serial_without_pallet = len(item.summary_out_serial_ids.filtered(
                lambda a: not a.pallet_id
            )) > 0

    @api.multi
    def _compute_manufacturing_pallet_ids(self):
        for item in self:
            pallet_ids = []
            for pallet_id in item.summary_out_serial_ids.mapped('pallet_id'):
                if pallet_id.id not in pallet_ids:
                    pallet_ids.append(pallet_id.id)
            if pallet_ids:
                item.manufacturing_pallet_ids = [(4, pallet_id) for pallet_id in pallet_ids]

    @api.onchange('qty_producing')
    def _onchange_qty_producing(self):
        print('se inhabilita este método')

    @api.multi
    def _compute_potential_lot_planned_ids(self):
        for item in self:
            item.potential_serial_planned_ids = self.env['stock.production.lot.serial'].search(
                [('reserved_to_production_id', '=', item.production_id.id), ('consumed', '=', True)])

    def _inverse_potential_lot_planned_ids(self):
        for item in self.potential_serial_planned_ids:
            item.update({
                'reserved_to_production_id': self.production_id.id,
                'consumed': True
            })

    @api.multi
    def _compute_summary_out_serial_ids(self):
        for item in self:
            if item.final_lot_id:
                item.summary_out_serial_ids = item.final_lot_id.stock_production_lot_serial_ids
                if item.byproduct_move_line_ids:
                    item.summary_out_serial_ids += item.byproduct_move_line_ids.mapped(
                        'lot_id'
                    ).mapped(
                        'stock_production_lot_serial_ids'
                    )
            else:
                item.summary_out_serial_ids = item.production_finished_move_line_ids.mapped(
                    'lot_id'
                ).mapped(
                    'stock_production_lot_serial_ids'
                )

    @api.multi
    def _compute_byproduct_move_line_ids(self):
        for item in self:
            item.byproduct_move_line_ids = item.active_move_line_ids.filtered(lambda a: not a.is_raw)

    @api.multi
    def _compute_material_product_ids(self):
        for item in self:
            item.material_product_ids = item.production_id.move_raw_ids.mapped('product_id')

    @api.model
    def create(self, values_list):
        res = super(MrpWorkorder, self).create(values_list)

        name = self.env['ir.sequence'].next_by_code('mrp.workorder')

        final_lot = self.env['stock.production.lot'].create({
            'name': name,
            'product_id': res.product_id.id,
            'is_prd_lot': True,
            'can_add_serial': True,
            'label_durability_id': res.production_id.label_durability_id.id
        })
        res.final_lot_id = final_lot.id
        return res

    @api.multi
    def write(self, vals):
        for item in self:
            if item.active_move_line_ids and \
                    not item.active_move_line_ids.filtered(lambda a: a.is_raw):
                for move_line in item.active_move_line_ids:
                    move_line.update({
                        'is_raw': True
                    })

        res = super(MrpWorkorder, self).write(vals)
        return res

    def open_tablet_view(self):
        while self.current_quality_check_id:
            check = self.current_quality_check_id
            if not check.component_is_byproduct:
                check.qty_done = 0
                self.action_skip()
            else:
                if not check.lot_id:
                    lot_tmp = self.env['stock.production.lot'].create({
                        'name': self.env['ir.sequence'].next_by_code('mrp.workorder'),
                        'product_id': check.component_id.id,
                        'is_prd_lot': True
                    })
                    check.lot_id = lot_tmp.id
                if check.quality_state == 'none':
                    super(MrpWorkorder,self).action_next()

        return super(MrpWorkorder, self).open_tablet_view()

    def action_next(self):
        self.validate_lot_code(self.lot_id.name)
        if self.current_quality_check_id.quality_state != 'none':
            for item in self.potential_serial_planned_ids.mapped('stock_production_lot_id'):
                stock_quant = item.get_stock_quant()
                stock_move = self.production_id.move_raw_ids.filtered(lambda a: a.product_id.id == item.product_id.id)
                virtual_location_production_id = self.env['stock.location'].search([
                    ('usage', '=', 'production'),
                    ('location_id.name', 'like', 'Virtual Locations')
                ])
                if item not in stock_move.active_move_line_ids.mapped('lot_id'):
                    stock_move.update({
                        'active_move_line_ids': [
                            (0, 0, {
                                'product_id': item.product_id.id,
                                'lot_id': item.id,
                                'qty_done': sum(self.potential_serial_planned_ids.filtered(
                                    lambda a: a.stock_production_lot_id.id == item.id).mapped('display_weight')),
                                'lot_produced_id': self.final_lot_id,
                                'product_uom_id': stock_move.product_uom.id,
                                'location_id': stock_quant.location_id.id,
                                'location_dest_id': virtual_location_production_id.id
                            })
                        ]
                    })
                    self.qty_done = 0
                    super(MrpWorkorder, self).action_skip()
                else:
                    for line in stock_move.active_move_line_ids:
                        if line.lot_id.id == item.id:
                            line.update({
                                'qty_done': sum(self.potential_serial_planned_ids.filtered(
                                    lambda a: a.stock_production_lot_id.id == item.id).mapped('display_weight'))
                            })
                    super(MrpWorkorder, self).action_skip()
        self.qty_done = 0

    @api.multi
    def organize_move_line(self):
        for move in self.production_id.move_raw_ids:
            for active in move.active_move_line_ids:
                if active.product_qty > 0:
                    active.unlink()
        for item in self.potential_serial_planned_ids.mapped('stock_production_lot_id'):
            stock_quant = item.get_stock_quant()
            stock_move = self.production_id.move_raw_ids.filtered(lambda a: a.product_id.id == item.product_id.id)

            virtual_location_production_id = self.env['stock.location'].search([
                ('usage', '=', 'production'),
                ('location_id.name', 'like', 'Virtual Locations')
            ])
            if len(stock_move) > 1:
                stock_move[0].update({
                    'active_move_line_ids': [
                        (5)
                    ]
                })
                if item not in stock_move[1].active_move_line_ids.mapped('lot_id'):
                    stock_move[1].update({
                        'active_move_line_ids': [
                            (0, 0, {
                                'product_id': item.product_id.id,
                                'lot_id': item.id,
                                'qty_done': sum(self.potential_serial_planned_ids.filtered(
                                    lambda a: a.stock_production_lot_id.id == item.id).mapped('display_weight')),
                                'lot_produced_id': self.final_lot_id,
                                'product_uom_id': stock_move[1].product_uom.id,
                                'location_id': stock_quant.location_id.id,
                                'location_dest_id': virtual_location_production_id.id
                            })
                        ]
                    })
                else:
                    for stock in stock_move:
                        for line in stock.active_move_line_ids:
                            if line.lot_id.id == item.id:
                                line.update({
                                    'qty_done': sum(self.potential_serial_planned_ids.filtered(
                                        lambda a: a.stock_production_lot_id.id == item.id).mapped('display_weight'))
                                })

            else:
                if item not in stock_move.active_move_line_ids.mapped('lot_id'):
                    stock_move.update({
                        'active_move_line_ids': [
                            (0, 0, {
                                'product_id': item.product_id.id,
                                'lot_id': item.id,
                                'qty_done': sum(self.potential_serial_planned_ids.filtered(
                                    lambda a: a.stock_production_lot_id.id == item.id).mapped('display_weight')),
                                'lot_produced_id': self.final_lot_id,
                                'product_uom_id': stock_move.product_uom.id,
                                'location_id': stock_quant.location_id.id,
                                'location_dest_id': virtual_location_production_id.id
                            })
                        ]
                    })
                else:
                    for line in stock_move.active_move_line_ids:
                        if line.lot_id.id == item.id:
                            line.update({
                                'qty_done': sum(self.potential_serial_planned_ids.filtered(
                                    lambda a: a.stock_production_lot_id.id == item.id).mapped('display_weight'))
                            })

    def action_skip(self):
        if self.qty_done > 0:
            raise models.ValidationError('Tiene que validar el kilos de ingresados')
        super(MrpWorkorder, self).action_skip()

    def action_ignore(self):
        for move in self.active_move_line_ids:
            if not move.lot_id:
                move.unlink()
        self.action_skip()
        for skip in self.skipped_check_ids:
            skip.unlink()

    @api.onchange('confirmed_serial')
    def confirmed_serial_keyboard(self):
        for item in self:
            res = item.on_barcode_scanned(item.confirmed_serial)
            if res and 'warning' in res and 'message' in res['warning']:
                raise models.ValidationError(res['warning']['message'])

    def on_barcode_scanned(self, barcode):
        qty_done = self.qty_done
        custom_serial = self.validate_serial_code(barcode)
        custom_serial.write({
            'reserved_to_production_id': self.production_id.id,
            'consumed': True
        })
        self.write({
            'potential_serial_planned_ids': [
                (4, custom_serial.id)
            ]
        })
        if custom_serial:
            barcode = custom_serial.stock_production_lot_id.name
        res = super(MrpWorkorder, self).on_barcode_scanned(barcode)
        if res:
            return res
        self.qty_done = qty_done + custom_serial.display_weight
        return res

    @api.model
    def lot_is_byproduct(self):
        return self.finished_product_check_ids.filtered(
            lambda a: a.lot_id == self.lot_id and a.component_is_byproduct
        )

    def validate_lot_code(self, lot_code):
        if not self.lot_is_byproduct():
            lot_search = self.env['stock.production.lot'].search([
                ('name', '=', lot_code)
            ])

    def validate_serial_code(self, barcode):
        custom_serial = self.env['stock.production.lot.serial'].search([('serial_number', '=', barcode)])
        if custom_serial:
            if custom_serial.product_id != self.component_id:
                raise models.ValidationError('El producto ingresado no corresponde al producto solicitado')
            if custom_serial.consumed:
                raise models.ValidationError('este código ya ha sido consumido en la produccion {}'.format(
                    custom_serial.reserved_to_production_id.name))
            return custom_serial
        # self.validate_lot_code(barcode)
        else:
            custom_serial = self.env['stock.production.lot.serial'].search([('serial_number', '=', barcode)])
        return custom_serial

    def open_out_form_view(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.workorder',
            'views': [[self.env.ref('dimabe_manufacturing.mrp_workorder_out_form_view').id, 'form']],
            'res_id': self.id,
            'target': 'fullscreen'
        }

    def create_pallet(self):
        default_product_id = None
        if 'default_product_id' in self.env.context:
            default_product_id = self.env.context['default_product_id']
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'manufacturing.pallet',
            'views': [[self.env.ref('dimabe_manufacturing.manufacturing_pallet_form_view').id, 'form']],
            'target': 'fullscreen',
            'context': {'_default_product_id': default_product_id}
        }
