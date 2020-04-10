from odoo import fields, models, api
from dateutil.relativedelta import relativedelta
from odoo.addons import decimal_precision as dp
import math


class StockProductionLotSerial(models.Model):
    _inherit = 'stock.production.lot.serial'

    production_id = fields.Many2one(
        'mrp.production',
        'Producción'
    )

    producer_id = fields.Many2one(
        'res.partner',
        'Productor'
    )

    product_variety = fields.Char(
        'Variedad',
        related='stock_production_lot_id.product_variety'
    )

    product_id = fields.Many2one(
        'product.product',
        related='stock_production_lot_id.product_id',
        string='Producto'
    )

    belongs_to_prd_lot = fields.Boolean(
        'pertenece a lote productivo',
        related='stock_production_lot_id.is_prd_lot'
    )

    reserved_to_production_id = fields.Many2one(
        'mrp.production',
        'Para Producción',
        nullable=True
    )

    stock_product_id = fields.Many2one(
        'product.product',
        related='stock_production_lot_id.product_id',
        string='Producto'
    )

    reserved_to_stock_picking_id = fields.Many2one(
        'stock.picking',
        'Para Picking',
        nullable=True
    )

    validate_to_stock_picking_id = fields.Many2one(
        'stock.picking',
        'Validado',
        nullable=True
    )

    is_dried_serial = fields.Boolean(
        'Es Serie Secada',
        related='stock_production_lot_id.is_dried_lot'
    )

    consumed = fields.Boolean('Consumido')

    confirmed_serial = fields.Char('Confimación de Serie')

    pallet_id = fields.Many2one(
        'manufacturing.pallet',
        'Pallet'
    )

    packaging_date = fields.Date(
        'Fecha Producción',
        default=fields.Date.today()
    )

    best_before_date = fields.Date(
        'Consumir antes de',
        compute='_compute_best_before_date'
    )

    harvest = fields.Integer(
        'Año de Cosecha',
        compute='_compute_harvest',
        # store=True
    )

    canning_id = fields.Many2one(
        'product.product',
        'Envase',
        inverse='_inverse_gross_weight'
    )

    gross_weight = fields.Float(
        'Peso Bruto',
        digits=dp.get_precision('Product Unit of Measure'),
        inverse='_inverse_gross_weight'
    )

    label_durability_id = fields.Many2one(
        'label.durability',
        'Dirabilidad Etiqueta'
    )

    label_percent = fields.Float(
        '% Peso Etiqueta',
        digits=dp.get_precision('Product Unit of Measure'),
        compute='_compute_label_percent'
    )

    bom_id = fields.Many2one(
        'mrp.bom',
        'Lista de Materiales',
        related='production_id.bom_id'
    )

    @api.multi
    def _inverse_real_weight(self):
        for item in self:
            item.real_weight = item.display_weight
            if not item.is_dried_serial:
                canning_weight = item.canning_id.weight
                if not canning_weight:
                    canning_weight = sum(item.get_possible_canning_id().mapped('weight'))
                item.gross_weight = item.display_weight + canning_weight

    def _inverse_gross_weight(self):
        if self.is_dried_serial:
            gross_weight_without_canning = self.gross_weight - self.canning_id.weight
            self.display_weight = gross_weight_without_canning - (gross_weight_without_canning * self.label_percent)

    @api.multi
    def _compute_label_percent(self):
        for item in self:
            settings_percent = float(self.env['ir.config_parameter'].sudo().get_param(
                'dimabe_manufacturing.label_percent_subtract'
            ))

            if settings_percent:
                item.label_percent = settings_percent / 100

    @api.multi
    # @api.depends('packaging_date')
    def _compute_harvest(self):
        for item in self:
            item.harvest = item.packaging_date.year

    @api.multi
    def _compute_best_before_date(self):
        for item in self:
            months = item.label_durability_id.month_qty
            item.best_before_date = item.packaging_date + relativedelta(months=months)

    @api.model
    def create(self, values_list):
        res = super(StockProductionLotSerial, self).create(values_list)

        if res.display_weight == 0 and res.gross_weight == 0:
            raise models.ValidationError('debe agregar un peso a la serie')

        stock_move_line = self.env['stock.move.line'].search([
            ('lot_id', '=', res.stock_production_lot_id.id),
            ('lot_id.is_prd_lot', '=', True)
        ])
        production = None
        if stock_move_line.mapped('move_id.production_id'):
            production = stock_move_line.mapped('move_id.production_id')[0]
            res.producer_id = res.stock_production_lot_id.producer_id.id
        else:
            work_order = self.env['mrp.workorder'].search([
                ('final_lot_id', '!=', False),
                ('final_lot_id', '=', res.stock_production_lot_id.id)
            ])

            res.producer_id = res.stock_production_lot_id.producer_id.id

            if work_order.production_id:
                production = work_order.production_id[0]

        if production:
            res.production_id = production.id
            res.reserve_to_stock_picking_id = production.stock_picking_id.id

        res.label_durability_id = res.stock_production_lot_id.label_durability_id

        if res.bom_id:
            if res.bom_id.product_id != res.product_id:
                res.gross_weight = res.display_weight
                return res
            res.set_bom_canning()
            if res.canning_id:
                res.gross_weight = res.display_weight + res.canning_id.weight
            else:
                res.gross_weight = res.display_weight + sum(res.get_possible_canning_id().mapped('weight'))
        return res

    @api.model
    def set_bom_canning(self):
        canning_id = self.get_possible_canning_id()
        if len(canning_id) == 1:
            self.canning_id = canning_id[0]

    @api.model
    def get_possible_canning_id(self):
        return self.bom_id.bom_line_ids.filtered(
            lambda a: 'envases' in str.lower(a.product_id.categ_id.name) or
                      'embalaje' in str.lower(a.product_id.categ_id.name)
                      or (
                              a.product_id.categ_id.parent_id and (
                              'envases' in str.lower(a.product_id.categ_id.parent_id.name) or
                              'embalaje' in str.lower(a.product_id.categ_id.parent_id.name))
                      )
        ).mapped('product_id')

    @api.multi
    def write(self, vals):
        res = super(StockProductionLotSerial, self).write(vals)

        for item in self:
            if item.display_weight == 0 and item.gross_weight == 0:
                raise models.ValidationError('debe agregar un peso a la serie')
            if not item.canning_id and item.bom_id:
                item.set_bom_canning()
        return res

    @api.model
    def unlink(self):
        if self.consumed:
            raise models.ValidationError(
                'este código {} ya fue consumido, no puede ser eliminado'.format(
                    self.serial_number
                )

            )
        return super(StockProductionLotSerial, self).unlink()

    @api.multi
    def print_serial_label(self):
        if 'producer_id' in self.env.context:
            for item in self:
                item.producer_id = self.env.context['producer_id']

        return self.env.ref(
            'dimabe_manufacturing.action_stock_production_lot_serial_label_report'
        ).report_action(self)

    @api.multi
    def get_full_url(self):
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return base_url

    @api.multi
    def reserve_serial(self):
        if 'mrp_production_id' in self.env.context:
            production = self.env['mrp.production'].search([('id', '=', self.env.context['mrp_production_id'])])
            from_lot = self.env.context['from_lot']
            if not production:
                raise models.ValidationError('No se encontró la orden de producción a la que reservar el producto')
            for item in self:
                if from_lot:
                    item.update({
                        'reserved_to_production_id': production.id
                    })

                    item.stock_production_lot_id.update({
                        'qty_to_reserve': item.stock_production_lot_id.balance
                    })
                else:
                    item.update({
                        'reserved_to_production_id': production.id
                    })

                    stock_move = production.move_raw_ids.filtered(
                        lambda a: a.product_id == item.stock_production_lot_id.product_id
                    )

                    stock_quant = item.stock_production_lot_id.get_stock_quant()

                    stock_quant.sudo().update({
                        'reserved_quantity': stock_quant.total_reserved
                    })

                    for stock in stock_move:
                        item.add_move_line(stock)
        else:
            raise models.ValidationError('no se pudo identificar producción')

    @api.model
    def add_move_line(self, stock_move):
        stock_quant = self.stock_production_lot_id.get_stock_quant()
        virtual_location_production_id = self.env['stock.location'].search([
            ('usage', '=', 'production'),
            ('location_id.name', 'like', 'Virtual Locations')
        ])
        stock_move.sudo().update({
            'active_move_line_ids': [
                (0, 0, {
                    'product_id': self.stock_production_lot_id.product_id.id,
                    'lot_id': self.stock_production_lot_id.id,
                    'product_uom_qty': self.display_weight,
                    'product_uom_id': stock_move.product_uom.id,
                    'location_id': stock_quant.location_id.id,
                    'location_dest_id': virtual_location_production_id.id
                })
            ]
        })

    @api.multi
    def unreserved_serial(self):
        for item in self:

            if item.consumed:
                raise models.ValidationError('el código {} ya ha sido consumido'.format(
                    item.name
                ))

            stock_move = item.reserved_to_production_id.move_raw_ids.filtered(
                lambda a: a.product_id == item.stock_production_lot_id.product_id
            )

            move_line = stock_move.active_move_line_ids.filtered(
                lambda a: a.lot_id.id == item.stock_production_lot_id.id and a.product_qty == item.display_weight
                          and a.qty_done == 0
            )

            stock_quant = item.stock_production_lot_id.get_stock_quant()

            item.update({
                'reserved_to_production_id': None
            })

            stock_quant.sudo().update({
                'reserved_quantity': stock_quant.total_reserved
            })

            if move_line:
                move_line[0].write({'move_id': None, 'product_uom_qty': 0})

    @api.multi
    def reserve_picking(self):
        models._logger.error('linea {330} reserve picking')
        # if 'stock_picking_id' in self.env.context:
        #     # stock_picking_id = self.env.context['stock_picking_id']
        #     # stock_picking = self.env['stock.picking'].search([('id', '=', stock_picking_id)])
        #     #
        #     # if not stock_picking:
        #     #     raise models.ValidationError('No se encontró el picking al que reservar el stock')
        #     #
        #     # for item in self:
        #     #     item.update({
        #     #         'reserved_to_stock_picking_id': stock_picking.id
        #     #     })
        #     #     stock_move = item.reserved_to_stock_picking_id.move_lines.filtered(
        #     #         lambda a: a.product_id == item.stock_production_lot_id.product_id
        #     #     )
        #     #
        #     #     stock_quant = item.stock_production_lot_id.get_stock_quant()
        #     #
        #     #     if not stock_quant:
        #     #         raise models.ValidationError('El lote {} aún se encuentra en proceso.'.format(
        #     #             item.stock_production_lot_id.name
        #     #         ))
        #     #
        #     #     move_line = self.env['stock.move.line'].create({
        #     #         'product_id': item.stock_production_lot_id.product_id.id,
        #     #         'lot_id': item.stock_production_lot_id.id,
        #     #         'product_uom_qty': item.display_weight,
        #     #         'product_uom_id': stock_move.product_uom.id,
        #     #         'location_id': stock_quant.location_id.id,
        #     #         # 'qty_done': item.display_weight,
        #     #         'location_dest_id': stock_picking.partner_id.property_stock_customer.id
        #     #     })
        #     #
        #     #     stock_move.sudo().update({
        #     #         'move_line_ids': [
        #     #             (4, move_line.id)
        #     #         ]
        #     #     })
        #     #
        #     #     item.reserved_to_stock_picking_id.update({
        #     #         'move_line_ids': [
        #     #             (4, move_line.id)
        #     #         ]
        #     #     })
        #     #
        #     #     stock_quant.sudo().update({
        #     #         'reserved_quantity': stock_quant.total_reserved
        #     #     })
        # else:
        #     raise models.ValidationError('no se pudo identificar picking')

    @api.multi
    def unreserved_picking(self):
        for item in self:
            stock_move = item.reserved_to_stock_picking_id.move_lines.filtered(
                lambda a: a.product_id == item.stock_production_lot_id.product_id
            )
            stock_picking = item.reserved_to_stock_picking_id.id
            move_line = stock_move.move_line_ids.filtered(
                lambda
                    a: a.lot_id.id == item.stock_production_lot_id.id
            )
            if len(move_line) > 1:
                for move in move_line:
                    picking_move_line = item.reserved_to_stock_picking_id.move_line_ids.filtered(
                        lambda a: a.id == move.id
                    )
                    stock_quant = item.stock_production_lot_id.get_stock_quant()

                    stock_quant.sudo().update({
                        'reserved_quantity': stock_quant.total_reserved
                    })

                    item.update({
                        'reserved_to_stock_picking_id': None
                    })

                    for ml in move:
                        if ml.qty_done > 0:
                            raise models.ValidationError('este producto ya ha sido validado')
                        ml.update({'move_id': None, 'product_uom_qty': 0})
                        picking_move_line.filtered(lambda a: a.id == ml.id).update({
                            'move_id': None,
                            'picking_id': None,
                            'product_uom_qty': item.stock_production_lot_id.available_total_serial - item.display_weight
                        })
            else:
                picking_move_line = item.reserved_to_stock_picking_id.move_line_ids.filtered(
                    lambda a: a.id == move_line.id
                )

                stock_quant = item.stock_production_lot_id.get_stock_quant()

                item.update({
                    'reserved_to_stock_picking_id': None
                })

                for ml in move_line:
                    if ml.qty_done > 0:
                        raise models.ValidationError('este producto ya ha sido validado')
                    ml.update({'move_id': None, 'product_uom_qty': ml.product_uom_qty - item.display_weight})
                    picking_move_line.filtered(lambda a: a.id == ml.id).update({
                        'move_id': ml.id,
                        'picking_id': stock_picking,
                        'product_uom_qty': ml.product_uom_qty
                    })
                stock_quant.sudo().update({
                    'reserved_quantity': stock_quant.total_reserved
                })

    def remove_and_reduce(self):
        if self.consumed:
            raise models.ValidationError('esta serie ya fue consumida')

        wo = self.env['mrp.workorder'].search([
            ('production_id', '=', self.reserved_to_production_id.id)
        ])

        if not wo:
            raise models.ValidationError('no se encontró orden de trabajo a reducir')

        if len(wo) > 1:
            raise models.ValidationError('existen {} ordenes asociadas a esta producción')

        moves = wo.move_raw_ids.filtered(
            lambda m: m.state not in ('done', 'cancel') and m.product_id == self.product_id)

        qty_producing = (wo.qty_producing * sum(moves.mapped('unit_factor'))) - self.display_weight

        wo.write({
            'qty_producing': qty_producing / sum(moves.mapped('unit_factor')),
        })

        self.reserved_to_production_id.write({
            'product_qty': qty_producing / sum(moves.mapped('unit_factor'))
        })

        done_qty = sum(wo.check_ids.filtered(
            lambda a: a.component_id == self.product_id and a.quality_state == 'pass'
        ).mapped('qty_done'))

        if done_qty >= qty_producing / sum(moves.mapped('unit_factor')):
            pending_checks = wo.check_ids.filtered(
                lambda a: a.component_id == self.product_id and a.quality_state == 'none'
            )

            if pending_checks:

                line = wo.active_move_line_ids.filtered(
                    lambda a: a.product_id == self.product_id and not a.lot_id
                )

                pending_checks.sudo().unlink()
                line.unlink()

                if wo.current_quality_check_id in pending_checks:
                    wo._change_quality_check(increment=1, children=1)

        production_move = self.reserved_to_production_id.move_raw_ids.filtered(
            lambda a: a.product_id == self.product_id
        )

        production_move.product_uom_qty = qty_producing

        reserved_serials = self.env['stock.production.lot.serial'].search([
            ('reserved_to_production_id', '=', self.reserved_to_production_id.id),
            ('id', '!=', self.id)
        ])

        self.unreserved_serial()

        if reserved_serials and not production_move.active_move_line_ids:
            for serial in reserved_serials:
                serial.add_move_line(production_move)
