from odoo import models, api, fields


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'barcodes.barcode_events_mixin']

    has_mrp_production = fields.Boolean('tiene orden de producción')

    shipping_id = fields.Many2one(
        'custom.shipment',
        'Embarque'
    )

    required_loading_date = fields.Date(
        related='shipping_id.required_loading_date')

    variety = fields.Many2many(related="product_id.attribute_value_ids")

    country_id = fields.Char(related='partner_id.country_id.name')

    product_id = fields.Many2one(related="move_ids_without_package.product_id")

    quantity_requested = fields.Float(
        related='move_ids_without_package.product_uom_qty')

    packing_list_ids = fields.One2many(
        'stock.production.lot.serial',
        compute='_compute_packing_list_ids'
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

    have_series = fields.Boolean('Tiene Serie', default=True, compute='_compute_potential_lot_serial_ids')

    @api.multi
    @api.depends('product_search_id')
    def _compute_potential_lot_serial_ids(self):
        for item in self:
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
            if item.product_search_id:
                domain += [('stock_product_id', '=',
                            item.product_search_id.id)]
            item.potential_lot_serial_ids = self.env['stock.production.lot.serial'].search(
                domain)

    @api.multi
    def _compute_potential_lot(self):
        for item in self:
            if not item.have_series:
                for product in item.move_ids_without_package.mapped('product_id.id'):
                    data = self.env['stock.production.lot.serial'].search([('stock_product_id', '=', product)])
                    if not data:
                        lot = self.env['stock.production.lot'].search([('product_id', '=', product)])
                        item.potential_lot_ids = lot

    @api.multi
    def _compute_packing_list_ids(self):
        for item in self:
            reserved_serial_ids = self.env['stock.production.lot.serial'].search([
                ('reserved_to_stock_picking_id', '=', item.id)
            ])
            item.packing_list_ids = reserved_serial_ids

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
    def button_validate(self):

        for serial in self.packing_list_ids:
            serial.update({
                'consumed': True
            })

        return super(StockPicking, self).button_validate()

    def validate_barcode(self, barcode):
        custom_serial = self.packing_list_ids.filtered(
            lambda a: a.serial_number == barcode
        )
        if not custom_serial:
            raise models.ValidationError('Esta serie no esta en packing list')
        return custom_serial

    @api.onchange('_barcode_scanned')
    def lala(self):
        raise models.ValidationError('lala')

    def on_barcode_scanned(self, barcode):

        raise models.ValidationError(barcode)

        for item in self:
            custom_serial = item.validate_barcode(barcode)
            if custom_serial.consumed:
                raise models.ValidationError('Serie ya fue consumida')
            stock_move = self.move_line_ids_without_package.filtered(
                lambda a: a.product_id == custom_serial.stock_production_lot_id.product_id
            )

            move_line = stock_move.filtered(
                lambda a: a.lot_id == custom_serial.stock_production_lot_id
            )
            if len(move_line) > 1:
                move_line[0].update({
                    'qty_done': move_line[0].qty_done + custom_serial.display_weight
                })
            else:
                move_line.update({
                    'qty_done': move_line.qty_done + custom_serial.display_weight
                })
            custom_serial.sudo().update(
                {
                    'consumed': True
                }
            )
