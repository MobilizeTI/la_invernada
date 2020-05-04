from odoo import fields, models, api
from odoo.addons import decimal_precision as dp
from datetime import datetime
import inspect


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    positioning_state = fields.Selection([
        ('pending', 'Pendiente'),
        ('done', 'Listo')
    ],
        'Estado movimiento de bodega a producción',
        default='pending'
    )

    client_id = fields.Many2one(
        'res.partner',
        related='stock_picking_id.partner_id',
        string='Cliente',
        readonly=True
    )

    destiny_country_id = fields.Many2one(
        'res.country',
        related='stock_picking_id.shipping_id.arrival_port.country_id',
        string='País'
    )

    charging_mode = fields.Selection(
        related='stock_picking_id.charging_mode',
        string='Modo de Carga'
    )

    client_label = fields.Boolean(
        'Etiqueta Cliente',
        related='stock_picking_id.client_label'
    )

    unevenness_percent = fields.Float(
        '% Descalibre',
        digits=dp.get_precision('Product Unit of Measure')
    )

    etd = fields.Date(
        'Fecha Despacho',
        related='stock_picking_id.shipping_id.etd'
    )

    observation = fields.Text('Observación')

    label_durability_id = fields.Many2one(
        'label.durability',
        'Durabilidad Etiqueta'
    )

    pt_balance = fields.Float(
        'Saldo Bodega PT',
        digits=dp.get_precision('Product Unit of Measure'),
        compute='_compute_pt_balance'
    )

    stock_picking_id = fields.Many2one('stock.picking', 'Despacho')

    sale_order_id = fields.Many2one(
        'sale.order',
        related='stock_picking_id.sale_id'
    )

    stock_lots = fields.Many2one("stock.production.lot")

    client_search_id = fields.Many2one(
        'res.partner',
        'Buscar Cliente',
        nullable=True
    )

    show_finished_move_line_ids = fields.One2many(
        'stock.move.line',
        compute='_compute_show_finished_move_line_ids'
    )

    consumed_material_ids = fields.One2many(
        'stock.production.lot.serial',
        related='workorder_ids.potential_serial_planned_ids'
    )

    required_date_moving_to_production = fields.Datetime(
        'Fecha Requerida de Movimiento a Producción',
        default=datetime.utcnow()
    )

    product_search_id = fields.Many2one(
        'product.product',
        'Buscar Producto',
        nullable=True,
    )

    product_lot = fields.Many2one(
        'product.product',
        related="stock_lots.product_id"
    )

    requested_qty = fields.Float(
        'Cantidad Solicitada',
        digits=dp.get_precision('Product Unit of Measure')
    )

    serial_lot_ids = fields.One2many(
        'stock.production.lot.serial',
        related="stock_lots.stock_production_lot_serial_ids"
    )

    potential_lot_ids = fields.One2many(
        'potential.lot',
        'mrp_production_id',
        'Posibles Lotes'
    )

    materials = fields.Many2many('product.product', compute='get_product_bom')

    manufactureable = fields.Many2many('product.product', compute='get_product_route')

    @api.multi
    def fix_moves(self):
        for item in self:
            for move in item.move_raw_ids:
                for line in move.active_move_line_ids:
                    raise models.ValidationError(move.active_move_line_ids.mapped('lot_id'))

    @api.multi
    def _compute_pt_balance(self):
        for item in self:
            item.pt_balance = sum(item.stock_picking_id.packing_list_ids.filtered(
                lambda a: a.production_id != item
            ).mapped('display_weight'))

    @api.model
    def get_product_route(self):
        list = []
        for item in self:
            products = item.env['product.product'].search([])
            for p in products:
                if "Fabricar" in p.route_ids.mapped('name'):
                    list.append(p.id)
            item.manufactureable = item.env['product.product'].search([('id', 'in', list)])

    @api.multi
    def get_product_bom(self):
        for item in self:
            item.update({
                'materials': item.bom_id.bom_line_ids.mapped('product_id')
            })

    @api.multi
    def _compute_show_finished_move_line_ids(self):
        for item in self:
            for move_line in item.finished_move_line_ids:
                existing_move = item.show_finished_move_line_ids.filtered(
                    lambda a: a.lot_id == move_line.lot_id
                )
                if not existing_move:
                    move_line.write({
                        'tmp_qty_done': move_line.qty_done
                    })
                    item.show_finished_move_line_ids += move_line
                else:
                    existing_move.write({
                        'tmp_qty_done': existing_move.tmp_qty_done + move_line.qty_done
                    })

    @api.model
    def get_potential_lot_ids(self):
        domain = [
            ('balance', '>', 0),
            ('product_id.id', 'in', list(self.move_raw_ids.filtered(
                lambda a: not a.product_id.categ_id.reserve_ignore
            ).mapped('product_id.id'))),
        ]
        if self.product_search_id:
            domain += [('product_id.id', '=', self.product_search_id.id)]

        if self.client_search_id:
            client_lot_ids = self.env['quality.analysis'].search([
                ('potential_client_id', '=', self.client_search_id.id),
                ('potential_workcenter_id.id', 'in', list(self.routing_id.operation_ids.mapped('workcenter_id.id')))
            ]).mapped('stock_production_lot_ids.name')

            domain += [('name', 'in', list(client_lot_ids) if client_lot_ids else [])]

        res = self.env['stock.production.lot'].search(domain)

        return [{
            'stock_production_lot_id': lot.id,
            'mrp_production_id': self.id
        } for lot in res]

    @api.multi
    def set_stock_move(self):
        product = self.env['stock.move'].create({'product_id': self.product_id})
        product_qty = self.env['stock.move'].create({'product_qty': self.product_qty})
        self.env.cr.commit()

    @api.multi
    def calculate_done(self):
        for item in self:
            lot = item.finished_move_line_ids.mapped('lot_id')
            for line_id in item.finished_move_line_ids:
                line_id.qty_done = line_id.lot_id.total_serial
            for move in item.move_raw_ids.filtered(
                    lambda a: a.product_id not in item.consumed_material_ids.mapped(
                        'product_id') and a.needs_lots is False
            ):
                move.quantity_done = sum(lot.mapped('count_serial')) * sum(item.bom_id.bom_line_ids.filtered(
                    lambda a: a.product_id == move.product_id
                ).mapped('product_qty'))

    @api.multi
    def button_mark_done(self):
        self.calculate_done()
        res = super(MrpProduction, self).button_mark_done()
        serial_to_reserve_ids = self.workorder_ids.mapped('production_finished_move_line_ids').mapped(
            'lot_id').filtered(
            lambda a: a.product_id in self.stock_picking_id.move_ids_without_package.mapped('product_id')
        ).mapped('stock_production_lot_serial_ids')

        # if serial_to_reserve_ids and len(serial_to_reserve_ids) > 0:
        #     serial_to_reserve_ids.write({
        #         'reserved_to_stock_picking_id': self.stock_picking_id.id
        #     })
        #
        # lot_id = serial_to_reserve_ids.mapped('stock_production_lot_id')
        # models._logger.error(lot_id)
        # for lot in lot_id:
        #     stock_move = self.stock_picking_id.move_lines.filtered(
        #             lambda a: a.product_id == lot.product_id
        #     )
        #
        #     stock_quant = lot.get_stock_quant()
        #
        #     if not stock_quant:
        #         raise models.ValidationError('El lote {} aún se encuentra en proceso.'.format(
        #             serial.stock_production_lot_id.name
        #     ))
        #
        #     potential_lot = self.env['potential.lot'].search([('stock_production_lot_id.id','=',lot.id)])
        #
        #     move_line = self.env['stock.move.line'].create({
        #         'product_id': lot.product_id.id,
        #         'lot_id': lot.id,
        #         'product_uom_qty': potential_lot.qty_to_reserve,
        #         'product_uom_id': stock_move.product_uom.id,
        #         'location_id': stock_quant.location_id.id,
        #         # 'qty_done': item.display_weight,
        #         'location_dest_id': self.stock_picking_id.partner_id.property_stock_customer.id
        #     })
        #
        #     stock_move.sudo().update({
        #         'move_line_ids': [
        #             (4, move_line.id)
        #             ]
        #         })
        #
        #     serial.reserved_to_stock_picking_id.update({
        #         'move_line_ids': [
        #             (4, move_line.id)
        #         ]
        #         })
        #
        #     stock_quant.sudo().update({
        #         'reserved_quantity': stock_quant.total_reserved
        #         })
        serial_to_reserve_ids.mapped('stock_production_lot_id').write({
            'can_add_serial': False
        })

        return res

    @api.model
    def create(self, values_list):
        res = super(MrpProduction, self).create(values_list)
        res.stock_picking_id.update({
            'has_mrp_production': True
        })
        return res

    # @api.multi
    # def action_cancel(self):
    #
    #     for lot in self.potential_lot_ids:
    #         stock_move = self.move_raw_ids.filtered(
    #             lambda a: a.product_id == lot.stock_production_lot_id.product_id
    #         )
    #
    #         move_line = stock_move.active_move_line_ids.filtered(
    #             lambda a: a.lot_id.id == lot.id and a.product_qty == lot.qty_to_reserve
    #                       and a.qty_done == 0
    #         )
    #         stock_quant = lot.get_stock_quant()
    #
    #         for serial in lot.stock_production_lot_id.stock_production_lot_serial_ids:
    #             serial.update({
    #                 'reserved_to_production_id': None
    #             })
    #
    #         stock_quant.sudo().update({
    #             'reserved_quantity': 0
    #         })
    #         if item.stock_picking_id:
    #             item.stock_picking_id.update({
    #                 'has_mrp_production': False
    #             })
    #             if move_line:
    #                 move_line[0].write({'move_id': None, 'product_uom_qty': 0})
    #             res = super(MrpProduction, self).action_cancel()
    #         else:
    #             res = super(MrpProduction,self).action_cancel()

    #
    #
    # @api.multi
    # def button_plan(self):
    #     for order in self:
    #         order.move_raw_ids.mapped('active_move_line_ids').mapped('lot_id').mapped(
    #             'stock_production_lot_serial_ids').filtered(lambda a: not a.consumed).update({
    #             'reserved_to_production_id': self.id

    #         res = super(MrpProduction, order).button_plan()
    #
    #         return res
