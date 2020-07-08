from odoo import fields, models, api
from odoo.addons import decimal_precision as dp
import xlsxwriter
from odoo.tools import float_compare, float_round
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
        string='Cliente',
        store=True
    )

    destiny_country_id = fields.Many2one(
        'res.country',
        related='production_id.destiny_country_id',
        string='País',
        store=True
    )

    sale_order_id = fields.Many2one(
        'sale.order',
        related='production_id.stock_picking_id.sale_id',
        string='Pedido de Venta',
        store=True
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

    lot_produced_id = fields.Integer('Lote a producir', compute='_compute_lot_produced')

    in_weight = fields.Float('Kilos Ingresados', compute='_compute_in_weight',
                             digits=dp.get_precision('Product Unit of Measure'), store=True)

    out_weight = fields.Float('Kilos Producidos', compute='_compute_out_weight',
                              digits=dp.get_precision('Product Unit of Measure'), store=True)

    pt_out_weight = fields.Float('Kilos Producidos del PT', compute='_compute_pt_out_weight',
                                 digits=dp.get_precision('Product Unit of Meausure'), store=True)

    producers_id = fields.Many2many('res.partner', 'Productores', compute='_compute_producers_id')

    pallet_qty = fields.Integer('Cantidad de Pallets', compute='_compute_pallet_qty')

    pallet_content = fields.Float('Kilos Totales', compute='_compute_pallet_content')

    pallet_serial = fields.Integer('Total de Series', compute='_compute_pallet_serial')

    @api.multi
    def _compute_pallet_content(self):
        for item in self:
            item.pallet_content = sum(item.manufacturing_pallet_ids.mapped('total_content_weight'))

    @api.multi
    def _compute_pallet_serial(self):
        for item in self:
            item.pallet_serial = len(item.manufacturing_pallet_ids.mapped('lot_serial_ids'))

    @api.multi
    def _compute_pallet_qty(self):
        for item in self:
            item.pallet_qty = len(item.manufacturing_pallet_ids)

    @api.multi
    def _compute_producers_id(self):
        for item in self:
            item.producers_id = item.potential_serial_planned_ids.mapped('producer_id')

    @api.depends('potential_serial_planned_ids')
    @api.multi
    def _compute_in_weight(self):
        for item in self:
            item.in_weight = sum(item.potential_serial_planned_ids.mapped('real_weight'))

    @api.depends('summary_out_serial_ids')
    @api.multi
    def _compute_out_weight(self):
        for item in self:
            item.out_weight = sum(item.summary_out_serial_ids.mapped('real_weight'))

    @api.depends('summary_out_serial_ids')
    @api.multi
    def _compute_pt_out_weight(self):
        for item in self:
            item.pt_out_weight = sum(
                item.summary_out_serial_ids.filtered(lambda a: 'PT' in a.product_id.default_code).mapped(
                    'real_weight'))

    @api.multi
    def show_in_serials(self):
        self.ensure_one()
        return {
            'name': "Series de Entrada",
            'view_type': 'form',
            'view_mode': 'tree,graph,form,pivot',
            'res_model': 'stock.production.lot.serial',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'views': [
                [self.env.ref('dimabe_manufacturing.stock_production_lot_serial_process_in_form_view').id, 'tree']],
            'context': self.env.context,
            'domain': [('id', 'in', self.potential_serial_planned_ids.mapped("id"))]
        }

    @api.multi
    def show_out_serials(self):
        self.ensure_one()
        return {
            'name': "Series de Salida",
            'view_type': 'form',
            'view_mode': 'tree,graph,form,pivot',
            'res_model': 'stock.production.lot.serial',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'views': [
                [self.env.ref('dimabe_manufacturing.stock_production_lot_serial_process_out_form_view').id, 'tree']],
            'context': self.env.context,
            'domain': [('id', 'in', self.summary_out_serial_ids.mapped("id"))]
        }

    @api.multi
    def _compute_lot_produced(self):
        for item in self:
            if len(item.production_finished_move_line_ids) > 1:
                item.lot_produced_id = item.production_finished_move_line_ids.filtered(
                    lambda a: a.product_id == item.product_id.id).lot_id.id
            item.lot_produced_id = item.final_lot_id.id

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
                    item.summary_out_serial_ids += item.byproduct_move_line_ids.filtered(
                        lambda a: a.lot_id not in item.potential_serial_planned_ids.mapped(
                            'stock_production_lot_id')).mapped(
                        'lot_id'
                    ).mapped(
                        'stock_production_lot_serial_ids'
                    )
            else:
                item.summary_out_serial_ids = item.production_finished_move_line_ids.filtered(
                    lambda a: a.lot_id not in item.potential_serial_planned_ids.mapped(
                        'stock_production_lot_id')).mapped(
                    'lot_id'
                ).mapped(
                    'stock_production_lot_serial_ids'
                )
            query = "UPDATE mrp_workorder set out_weight = {},pt_out_weight = {} where id = {}".format(
                sum(item.summary_out_serial_ids.mapped('real_weight')), sum(
                    item.summary_out_serial_ids.filtered(lambda a: a.product_id.id == item.product_id.id).mapped(
                        'real_weight')), item.id)
            cr = self._cr
            cr.execute(query)

    @api.multi
    def fix_order(self):
        for item in self:
            if item.final_lot_id:
                item.summary_out_serial_ids = item.final_lot_id.stock_production_lot_serial_ids
                if item.byproduct_move_line_ids:
                    item.summary_out_serial_ids += item.byproduct_move_line_ids.filtered(
                        lambda a: a.lot_id not in item.potential_serial_planned_ids).mapped(
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
                    check.qty_done = self.component_remaining_qty
                    if check.quality_state == 'none' and check.qty_done > 0:
                        self.action_next()

        self.action_first_skipped_step()
        return super(MrpWorkorder, self).open_tablet_view()

    def action_next(self):
        self.validate_lot_code(self.lot_id.name)
        super(MrpWorkorder, self).action_next()
        self.qty_done = 0

    @api.multi
    def organize_move_line(self):
        for move in self.production_id.move_raw_ids:
            for active in move.active_move_line_ids:
                active.unlink()
        for item in self.potential_serial_planned_ids.mapped('stock_production_lot_id'):
            stock_move = self.production_id.move_raw_ids.filtered(lambda a: a.product_id.id == item.product_id.id)
            virtual_location_production_id = self.env['stock.location'].search([
                ('usage', '=', 'production'),
                ('location_id.name', 'like', 'Virtual Locations')
            ])
            models._logger.error(stock_move.product_uom)
            if item not in stock_move.active_move_line_ids.mapped('lot_id'):
                if not item.location_id:
                    # item.location_id = item.stock_production_lot_serial_ids.mapped('production_id').location_dest_id
                    raise models.ValidationError("Lote {} aun esta en proceso {}".format(item.name, item.location_id))
                if not self.lot_produced_id:
                    stock_move.update({
                        'active_move_line_ids': [
                            (0, 0, {
                                'product_id': item.product_id.id,
                                'lot_id': item.id,
                                'qty_done': sum(self.potential_serial_planned_ids.filtered(
                                    lambda a: a.stock_production_lot_id.id == item.id).mapped('display_weight')),
                                'lot_produced_id': self.production_finished_move_line_ids.filtered(
                                    lambda a: a.product_id.id == self.product_id.id and a.lot_id).lot_id,
                                'workorder_id': self.id,
                                'production_id': self.production_id.id,
                                'product_uom_id': stock_move.product_uom.id,
                                'location_id': item.location_id.id,
                                'location_dest_id': virtual_location_production_id.id
                            })
                        ]
                    })
                else:
                    stock_move.update({
                        'active_move_line_ids': [
                            (0, 0, {
                                'product_id': item.product_id.id,
                                'lot_id': item.id,
                                'qty_done': sum(self.potential_serial_planned_ids.filtered(
                                    lambda a: a.stock_production_lot_id.id == item.id).mapped('display_weight')),
                                'lot_produced_id': self.lot_produced_id,
                                'workorder_id': self.id,
                                'production_id': self.production_id.id,
                                'product_uom_id': stock_move.product_uom.id,
                                'location_id': item.location_id.id,
                                'location_dest_id': virtual_location_production_id.id
                            })
                        ]
                    })

    def do_finish(self):
        self.write({
            'lot_produced_id': self.final_lot_id.id
        })
        if self.production_id.move_raw_ids.filtered(lambda a : not a.product_uom):
            raise models.ValidationError('{}'.format(self.production_id.move_raw_ids.filtered(lambda a : not a.product_uom)))
        super(MrpWorkorder, self).do_finish()
        self.organize_move_line()

    @api.multi
    def record_production(self):
        if not self:
            return True

        self.ensure_one()
        if self.qty_producing <= 0:
            raise models.UserError(('Please set the quantity you are currently producing. It should be different from zero.'))

        if (self.production_id.product_id.tracking != 'none') and not self.final_lot_id and self.move_raw_ids:
            raise models.UserError(('You should provide a lot/serial number for the final product.'))

        # Update quantities done on each raw material line
        # For each untracked component without any 'temporary' move lines,
        # (the new workorder tablet view allows registering consumed quantities for untracked components)
        # we assume that only the theoretical quantity was used
        for move in self.move_raw_ids:
            if not move.product_uom:
                raise models.UserError(move.id)
            if move.has_tracking == 'none' and (move.state not in ('done', 'cancel')) and move.bom_line_id \
                    and move.unit_factor and not move.move_line_ids.filtered(lambda ml: not ml.done_wo):
                rounding = move.product_uom.rounding
                if self.product_id.tracking != 'none':
                    qty_to_add = float_round(self.qty_producing * move.unit_factor, precision_rounding=rounding)
                    move._generate_consumed_move_line(qty_to_add, self.final_lot_id)
                elif len(move._get_move_lines()) < 2:
                    move.quantity_done += float_round(self.qty_producing * move.unit_factor,
                                                      precision_rounding=rounding)
                else:
                    move._set_quantity_done(move.quantity_done + float_round(self.qty_producing * move.unit_factor,
                                                                             precision_rounding=rounding))

        # Transfer quantities from temporary to final move lots or make them final
        for move_line in self.active_move_line_ids:
            # Check if move_line already exists
            if move_line.qty_done <= 0:  # rounding...
                move_line.sudo().unlink()
                continue
            if move_line.product_id.tracking != 'none' and not move_line.lot_id:
                raise models.UserError(('You should provide a lot/serial number for a component.'))
            # Search other move_line where it could be added:
            lots = self.move_line_ids.filtered(
                lambda x: (x.lot_id.id == move_line.lot_id.id) and (not x.lot_produced_id) and (not x.done_move) and (
                            x.product_id == move_line.product_id))
            if lots:
                lots[0].qty_done += move_line.qty_done
                lots[0].lot_produced_id = self.final_lot_id.id
                self._link_to_quality_check(move_line, lots[0])
                move_line.sudo().unlink()
            else:
                move_line.lot_produced_id = self.final_lot_id.id
                move_line.done_wo = True

        self.move_line_ids.filtered(
            lambda move_line: not move_line.done_move and not move_line.lot_produced_id and move_line.qty_done > 0
        ).write({
            'lot_produced_id': self.final_lot_id.id,
            'lot_produced_qty': self.qty_producing
        })

        # If last work order, then post lots used
        # TODO: should be same as checking if for every workorder something has been done?
        if not self.next_work_order_id:
            production_move = self.production_id.move_finished_ids.filtered(
                lambda x: (x.product_id.id == self.production_id.product_id.id) and (x.state not in ('done', 'cancel')))
            if production_move.product_id.tracking != 'none':
                move_line = production_move.move_line_ids.filtered(lambda x: x.lot_id.id == self.final_lot_id.id)
                if move_line:
                    move_line.product_uom_qty += self.qty_producing
                    move_line.qty_done += self.qty_producing
                else:
                    location_dest_id = production_move.location_dest_id.get_putaway_strategy(
                        self.product_id).id or production_move.location_dest_id.id
                    move_line.create({'move_id': production_move.id,
                                      'product_id': production_move.product_id.id,
                                      'lot_id': self.final_lot_id.id,
                                      'product_uom_qty': self.qty_producing,
                                      'product_uom_id': production_move.product_uom.id,
                                      'qty_done': self.qty_producing,
                                      'workorder_id': self.id,
                                      'location_id': production_move.location_id.id,
                                      'location_dest_id': location_dest_id,
                                      })
            else:
                production_move._set_quantity_done(self.qty_producing)

        if not self.next_work_order_id:
            for by_product_move in self._get_byproduct_move_to_update():
                if by_product_move.has_tracking != 'serial':
                    values = self._get_byproduct_move_line(by_product_move,
                                                           self.qty_producing * by_product_move.unit_factor)
                    self.env['stock.move.line'].create(values)
                elif by_product_move.has_tracking == 'serial':
                    qty_todo = by_product_move.product_uom._compute_quantity(
                        self.qty_producing * by_product_move.unit_factor, by_product_move.product_id.uom_id)
                    for i in range(0, int(float_round(qty_todo, precision_digits=0))):
                        values = self._get_byproduct_move_line(by_product_move, 1)
                        self.env['stock.move.line'].create(values)

        # Update workorder quantity produced
        self.qty_produced += self.qty_producing

        if self.final_lot_id:
            self.final_lot_id.use_next_on_work_order_id = self.next_work_order_id
            self.final_lot_id = False

        # One a piece is produced, you can launch the next work order
        self._start_nextworkorder()

        # Set a qty producing
        rounding = self.production_id.product_uom_id.rounding
        if float_compare(self.qty_produced, self.production_id.product_qty, precision_rounding=rounding) >= 0:
            self.qty_producing = 0
        elif self.production_id.product_id.tracking == 'serial':
            self._assign_default_final_lot_id()
            self.qty_producing = 1.0
            self._generate_lot_ids()
        else:
            self.qty_producing = float_round(self.production_id.product_qty - self.qty_produced,
                                             precision_rounding=rounding)
            self._generate_lot_ids()

        if self.next_work_order_id and self.next_work_order_id.state not in ['done',
                                                                             'cancel'] and self.production_id.product_id.tracking != 'none':
            self.next_work_order_id._assign_default_final_lot_id()

        if float_compare(self.qty_produced, self.production_id.product_qty, precision_rounding=rounding) >= 0:
            self.button_finish()
        return True


    def action_skip(self):
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
