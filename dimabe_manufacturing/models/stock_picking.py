from odoo import models, api, fields
from odoo.addons import decimal_precision as dp
import datetime
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
import datetime


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    has_mrp_production = fields.Boolean('tiene orden de producción')

    shipping_id = fields.Many2one(
        'custom.shipment',
        'Embarque'
    )

    required_loading_date = fields.Date(
        related='shipping_id.required_loading_date'
    )
    variety = fields.Many2many(related="product_id.attribute_value_ids")

    country_id = fields.Char(related='partner_id.country_id.name')

    product_id = fields.Many2one(related="move_ids_without_package.product_id")

    quantity_requested = fields.Float(
        related='move_ids_without_package.product_uom_qty',
        digits=dp.get_precision('Product Unit of Measure')
    )

    packing_list_ids = fields.One2many(
        'stock.production.lot.serial',
        'reserved_to_stock_picking_id'
    )

    product_search_id = fields.Many2one(
        'product.product',
        string='Buscar Producto',
    )

    potential_lot_serial_ids = fields.One2many(
        'stock.production.lot.serial',
        compute='_compute_potential_lot_serial_ids',
        string='Stock Disponibles',
    )

    potential_lot_ids = fields.One2many(
        'stock.production.lot',
        compute='_compute_potential_lot',
        string='Lotes Disponibles'
    )

    assigned_pallet_ids = fields.One2many(
        'manufacturing.pallet',
        'reserved_to_stock_picking_id'
    )

    have_series = fields.Boolean('Tiene Serie', default=True, compute='_compute_potential_lot_serial_ids')

    packing_list_lot_ids = fields.One2many(
        'stock.production.lot',
        compute='_compute_packing_list_lot_ids'
    )

    sale_order_id = fields.Many2one('sale.order', 'Pedido')

    sale_orders_id = fields.Many2one('sale.order', 'Pedidos', domain=[('state', '=', 'sale')])

    dispatch_line_ids = fields.One2many('custom.dispatch.line', 'dispatch_id')

    name_orders = fields.Char('Pedidos',compute='get_name_orders')

    dispatch_id = fields.Many2one('stock.picking','Despachos')

    real_net_weigth = fields.Float('Kilos Netos Reales',compute='compute_net_weigth_real')

    @api.multi
    def compute_net_weigth_real(self):
        for item in self:
            item.real_net_weigth = sum(item.packing_list_ids.mapped('display_weight'))

    @api.multi
    def get_name_orders(self):
        self.name_orders = ", ".join(self.dispatch_line_ids.mapped('sale_id').mapped('name'))

    @api.multi
    def add_orders_to_dispatch(self):
        if len(self.sale_orders_id.mapped('order_line')) > 0:
            for item in self.dispatch_id.mapped('move_ids_without_package'):
                if item.product_id.id not in self.move_ids_without_package.mapped('product_id').mapped('id'):
                    self.env['stock.move'].sudo().create({
                        'name': self.name,
                        'product_id': item.product_id.id,
                        'product_uom': item.product_id.uom_id.id,
                        'product_uom_qty': item.product_uom_qty,
                        'picking_id': self.id,
                        'location_id': self.location_id.id,
                        'location_dest_id': self.location_dest_id.id,
                        'date': datetime.datetime.now(),
                        'procure_method': 'make_to_stock'
                    })
                else:
                    move = self.move_ids_without_package.filtered(lambda a: a.product_id.id == item.product_id.id)
                    move.write({
                        'product_uom_qty':move.product_uom_qty + item.product_uom_qty
                    })
            for product_id in self.sale_orders_id.mapped('order_line').mapped('product_id'):
                self.env['custom.dispatch.line'].create({
                    'sale_id': self.sale_orders_id.id,
                    'product_id': product_id.id,
                    'dispatch_id': self.id,
                    'required_sale_qty': sum(self.sale_orders_id.mapped('order_line').filtered(lambda a: a.product_id.id == product_id.id).mapped('product_uom_qty'))
                })
            self.write({
                'is_principal_dispatch':True
            })

    @api.onchange('picking_type_code')
    def on_change_picking_type(self):
        for item in self:
            if item.picking_type_code == 'incoming':
                res = {
                    'domain': {
                        'partner_id': [('is_company', '=', True), ('supplier', '=', True), ('name', '!=', '')],
                    }
                }
            else:
                res = {
                    'domain': {
                        'partner_id': [('is_company', '=', True), ('customer', '=', True), ('name', '!=', '')],
                    }
                }
        return res

    @api.multi
    def remove_reserved_serial(self):
        lots = self.packing_list_ids.filtered(lambda a: a.to_delete ).mapped('stock_production_lot_id')
        self.packing_list_ids.filtered(lambda a: a.to_delete and a.reserved_to_stock_picking_id.id == self.id).write({
            'reserved_to_stock_picking_id': None,
            'to_delete': False
        })
        for lot in lots:
            move = self.move_line_ids_without_package.filtered(lambda a: a.lot_id.id == lot.id)
            quant = self.env['stock.quant'].search([('lot_id', '=', lot.id), ('location_id.usage', '=', 'internal')])
            qty_move = sum(lot.stock_production_lot_serial_ids.filtered(
                lambda a: a.reserved_to_stock_picking_id.id == self.id).mapped('display_weight'))
            reserved_qty = sum(
                lot.stock_production_lot_serial_ids.filtered(lambda a: a.reserved_to_stock_picking_id).mapped(
                    'display_weight'))
            quant.write({
                'reserved_quantity': reserved_qty if reserved_qty > 0 else 0
            })
            move.write({
                'product_uom_qty': qty_move if qty_move > 0 else 0
            })


    @api.multi
    def remove_reserved_pallet(self):
        lots = self.assigned_pallet_ids.filtered(lambda a: a.remove_picking).mapped('lot_id')
        pallet_to_remove = self.assigned_pallet_ids.filtered(lambda a: a.remove_picking and a.reserved_to_stock_picking_id.id == self.id)
        for pallet in pallet_to_remove:
            pallet.lot_serial_ids.filtered(lambda a: a.reserved_to_stock_picking_id.id == self.id).write({
                'reserved_to_stock_picking_id': None
            })
            pallet.write({
                'reserved_to_stock_picking_id': None,
                'remove_picking': False
            })
        for lot in lots:
            move = self.move_line_ids_without_package.filtered(lambda a: a.lot_id.id == lot.id)
            quant = self.env['stock.quant'].search([('lot_id','=',lot.id),('location_id.usage', '=', 'internal')])
            qty_move = sum(lot.stock_production_lot_serial_ids.filtered(lambda a: a.reserved_to_stock_picking_id.id == self.id).mapped('display_weight'))
            qty_quant = sum(lot.stock_production_lot_serial_ids.filtered(lambda a: not a.reserved_to_stock_picking_id).mapped('display_weight'))
            reserved_qty = sum(lot.stock_production_lot_serial_ids.filtered(lambda a: a.reserved_to_stock_picking_id).mapped('display_weight'))
            quant.write({
                'quantity': qty_quant if qty_quant > 0 else 0,
                'reserved_quantity':reserved_qty if reserved_qty > 0 else 0
            })
            move.write({
                'product_uom_qty': qty_move if qty_move > 0 else 0
            })


    @api.multi
    def _compute_packing_list_lot_ids(self):
        for item in self:
            if item.packing_list_ids and item.picking_type_code == 'outgoing':
                item.packing_list_lot_ids = item.packing_list_ids.mapped('stock_production_lot_id')
            else:
                item.packing_list_lot_ids = []

    @api.onchange('sale_order_id')
    def on_change_production_id(self):
        for item in self:
            if item.picking_type_code == 'outgoing':
                item.potential_lot_ids = self.env['stock.production.lot'].search(
                    [('sale_order_id', '=', item.sale_order_id.id),
                     ('product_id', '=', item.move_ids_without_package.mapped('product_id.id'))])

    @api.multi
    def _compute_potential_lot_serial_ids(self):
        for item in self:
            if item.picking_type_code == 'outgoing':
                domain = [
                    ('stock_product_id', 'in',
                     item.move_ids_without_package.mapped('product_id.id')),
                    ('consumed', '=', False),
                    ('reserved_to_stock_picking_id', '=', False)
                ]
                for id_pr in item.move_ids_without_package.mapped('product_id.id'):
                    data = self.env['stock.production.lot.serial'].search([('stock_product_id', '=', id_pr)])
                    if not data:
                        item.have_series = False

                item.potential_lot_serial_ids = self.env['stock.production.lot.serial'].search(
                    domain)

    @api.multi
    def calculate_last_serial(self):
        if self.picking_type_code == 'incoming':
            if len(canning) == 1:
                if self.production_net_weight == self.net_weight:
                    self.production_net_weight = self.net_weight - self.quality_weight

                self.env['stock.production.lot.serial'].search([('stock_production_lot_id', '=', self.name)]).write({
                    'real_weight': self.avg_unitary_weight
                })
                diff = self.production_net_weight - (canning.product_uom_qty * self.avg_unitary_weight)
                self.env['stock.production.lot.serial'].search([('stock_production_lot_id', '=', self.name)])[-1].write(
                    {
                        'real_weight': self.avg_unitary_weight + diff
                    })

    @api.multi
    def _compute_potential_lot(self):
        for item in self:
            if item.picking_type_code == 'outgoing':
                domain = [
                    ('product_id', 'in', item.move_ids_without_package.mapped('product_id.id')),
                    ('available_total_serial', '>', 0)
                ]
                lot = self.env['stock.production.lot'].search(domain)
                item.potential_lot_ids = lot

    @api.multi
    def return_action(self):
        context = {
            'default_product_id': self.product_id.id,
            'default_product_uom_qty': self.quantity_requested,
            'default_origin': self.name,
            'default_stock_picking_id': self.id,
            'default_client_search_id': self.partner_id.id,
            'default_requested_qty': self.quantity_requested
        }
        return {
            "type": "ir.actions.act_window",
            "res_model": "mrp.production",
            "view_type": "form",
            "view_mode": "form",
            "views": [(False, "form")],
            "view_id ref='mrp.mrp_production_form_view'": '',
            "target": "current",
            "context": context
        }

    @api.multi
    def action_confirm(self):
        res = super(StockPicking, self).action_confirm()
        for stock_picking in self:
            mp_move = stock_picking.get_mp_move()
            if stock_picking.picking_type_id.require_dried:
                for move_line in mp_move.move_line_ids:
                    move_line.lot_id.unpelled_state = 'waiting'
            mp_move.move_line_ids.mapped('lot_id').write({
                'stock_picking_id': stock_picking.id
            })
            for lot_id in mp_move.move_line_ids.mapped('lot_id'):
                if lot_id.stock_production_lot_serial_ids:
                    lot_id.stock_production_lot_serial_ids.write({
                        'producer_id': lot_id.stock_picking_id.partner_id.id
                    })
        return res

    @api.multi
    def button_validate(self):
        if self.picking_type_code == 'outgoing':
            return super(StockPicking, self).button_validate()

    def validate_barcode(self, barcode):
        custom_serial = self.packing_list_ids.filtered(
            lambda a: a.serial_number == barcode
        )
        if not custom_serial:
            raise models.ValidationError('el código {} no corresponde a este despacho'.format(barcode))
        return custom_serial

    def on_barcode_scanned(self, barcode):
        for item in self:
            custom_serial = item.validate_barcode(barcode)
            if custom_serial.consumed:
                raise models.ValidationError('el código {} ya fue consumido'.format(barcode))

            stock_move_line = self.move_line_ids_without_package.filtered(
                lambda a: a.product_id == custom_serial.stock_production_lot_id.product_id and
                          a.lot_id == custom_serial.stock_production_lot_id and
                          a.product_uom_qty == custom_serial.display_weight and
                          a.qty_done == 0
            )

            if len(stock_move_line) > 1:
                stock_move_line[0].write({
                    'qty_done': custom_serial.display_weight
                })
            else:
                stock_move_line.write({
                    'qty_done': custom_serial.display_weight
                })

            custom_serial.sudo().write({
                'consumed': True
            })
