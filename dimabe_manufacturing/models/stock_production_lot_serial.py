from odoo import fields, models, api
from dateutil.relativedelta import relativedelta
from odoo.addons import decimal_precision as dp


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
        store=True
    )

    gross_weight = fields.Float(
        'Peso Bruto',
        compute='_compute_gross_weight',
        digits=dp.get_precision('Peso Bruto')
    )

    @api.multi
    def _compute_gross_weight(self):
        for item in self:
            if item.stock_production_lot_id.oven_use_ids:
                unpelled_dried_id = item.stock_production_lot_id.oven_use_ids[0].unpelled_dried_id or \
                                    item.stock_production_lot_id.oven_use_ids[0].history_id
                canning_weight = 0
                models._logger.error(unpelled_dried_id)
                if unpelled_dried_id:
                    canning_weight = unpelled_dried_id.canning_id.weight
                item.gross_weight = item.display_weight + canning_weight

    @api.multi
    def _compute_harvest(self):
        for item in self:
            item.harvest = item.packaging_date.year

    @api.multi
    def _compute_best_before_date(self):
        for item in self:
            months = item.production_id.label_durability_id.month_qty or 0
            item.best_before_date = item.packaging_date + relativedelta(months=months)

    @api.model
    def create(self, values_list):
        res = super(StockProductionLotSerial, self).create(values_list)
        stock_move_line = self.env['stock.move.line'].search([
            ('lot_id', '=', res.stock_production_lot_id.id),
            ('lot_id.is_prd_lot', '=', True)
        ])
        production = None
        if stock_move_line.move_id.production_id:
            production = stock_move_line.move_id.production_id[0]
        else:
            work_order = self.env['mrp.workorder'].search([
                ('final_lot_id', '=', res.stock_production_lot_id.id)
            ])

            res.producer_id = res.stock_production_lot_id.producer_id.id

            if work_order.production_id:
                production = work_order.production_id[0]

        if production:
            res.production_id = production.id
            res.reserve_to_stock_picking_id = production.stock_picking_id.id

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
            production_id = self.env.context['mrp_production_id']
            production = self.env['mrp.production'].search([('id', '=', production_id)])
            if not production:
                raise models.ValidationError('No se encontró la orden de producción a la que reservar el producto')
            for item in self:
                item.update({
                    'reserved_to_production_id': production.id
                })

                stock_move = production.move_raw_ids.filtered(
                    lambda a: a.product_id == item.stock_production_lot_id.product_id
                )

                stock_quant = item.stock_production_lot_id.get_stock_quant()

                virtual_location_production_id = item.env['stock.location'].search([
                    ('usage', '=', 'production'),
                    ('location_id.name', 'like', 'Virtual Locations')
                ])

                stock_quant.sudo().update({
                    'reserved_quantity': stock_quant.reserved_quantity + item.display_weight
                })

                for stock in stock_move:
                    stock.sudo().update({
                        'active_move_line_ids': [
                            (0, 0, {
                                'product_id': item.stock_production_lot_id.product_id.id,
                                'lot_id': item.stock_production_lot_id.id,
                                'product_uom_qty': item.display_weight,
                                'product_uom_id': stock.product_uom.id,
                                'location_id': stock_quant.location_id.id,
                                'location_dest_id': virtual_location_production_id.id
                            })
                        ]
                    })
        else:
            raise models.ValidationError('no se pudo identificar producción')

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
            )

            stock_quant = item.stock_production_lot_id.get_stock_quant()
            stock_quant.sudo().update({
                'reserved_quantity': stock_quant.reserved_quantity - item.display_weight
            })

            item.update({
                'reserved_to_production_id': None
            })

            for ml in move_line:
                if ml.qty_done > 0:
                    raise models.ValidationError('este producto ya ha sido consumido')
                ml.write({'move_id': None, 'product_uom_qty': 0})

    @api.multi
    def reserve_picking(self):
        if 'stock_picking_id' in self.env.context:
            stock_picking_id = self.env.context['stock_picking_id']
            stock_picking = self.env['stock.picking'].search([('id', '=', stock_picking_id)])

            if not stock_picking:
                raise models.ValidationError('No se encontró el picking al que reservar el stock')
            for item in self:
                item.update({
                    'reserved_to_stock_picking_id': stock_picking.id
                })
                stock_move = item.reserved_to_stock_picking_id.move_lines.filtered(
                    lambda a: a.product_id == item.stock_production_lot_id.product_id
                )

                stock_quant = item.stock_production_lot_id.get_stock_quant()

                if not stock_quant:
                    raise models.ValidationError('El lote {} aún se encuentra en proceso.'.format(
                        item.stock_production_lot_id.name
                    ))

                stock_quant.sudo().update({
                    'reserved_quantity': stock_quant.reserved_quantity + item.display_weight
                })

                move_line = self.env['stock.move.line'].create({
                    'product_id': item.stock_production_lot_id.product_id.id,
                    'lot_id': item.stock_production_lot_id.id,
                    'product_uom_qty': item.display_weight,
                    'product_uom_id': stock_move.product_uom.id,
                    'location_id': stock_quant.location_id.id,
                    # 'qty_done': item.display_weight,
                    'location_dest_id': stock_picking.partner_id.property_stock_customer.id
                })

                stock_move.sudo().update({
                    'move_line_ids': [
                        (4, move_line.id)
                    ]
                })

                item.reserved_to_stock_picking_id.update({
                    'move_line_ids': [
                        (4, move_line.id)
                    ]
                })
        else:
            raise models.ValidationError('no se pudo identificar picking')

    @api.multi
    def unreserved_picking(self):
        for item in self:

            stock_move = item.reserved_to_stock_picking_id.move_lines.filtered(
                lambda a: a.product_id == item.stock_production_lot_id.product_id
            )
            move_line = stock_move.move_line_ids.filtered(
                lambda a: a.lot_id.id == item.stock_production_lot_id.id and a.product_qty == item.display_weight
            )
            if len(move_line) > 1:
                for move in move_line:

                    picking_move_line = item.reserved_to_stock_picking_id.move_line_ids.filtered(
                        lambda a: a.id == move.id
                    )

                    stock_quant = item.stock_production_lot_id.get_stock_quant()

                    stock_quant.sudo().update({
                        'reserved_quantity': stock_quant.reserved_quantity - item.display_weight
                    })

                    item.update({
                        'reserved_to_stock_picking_id': None
                    })

                    for ml in move:
                        if ml.qty_done > 0:
                            raise models.ValidationError('este producto ya ha sido validado')
                        ml.write({'move_id': None, 'product_uom_qty': 0})
                        picking_move_line.filtered(lambda a: a.id == ml.id).write({
                            'move_id': None,
                            'picking_id': None,
                            'product_uom_qty': 0
                        })
            else:
                picking_move_line = item.reserved_to_stock_picking_id.move_line_ids.filtered(
                    lambda a: a.id == move_line.id
                )

                stock_quant = item.stock_production_lot_id.get_stock_quant()

                stock_quant.sudo().update({
                    'reserved_quantity': stock_quant.reserved_quantity - item.display_weight
                })

                item.update({
                    'reserved_to_stock_picking_id': None
                })

                for ml in move_line:
                    if ml.qty_done > 0:
                        raise models.ValidationError('este producto ya ha sido validado')
                    ml.write({'move_id': None, 'product_uom_qty': 0})
                    picking_move_line.filtered(lambda a: a.id == ml.id).write({
                        'move_id': None,
                        'picking_id': None,
                        'product_uom_qty': 0,
                        'reserved_availability': 0
                    })
