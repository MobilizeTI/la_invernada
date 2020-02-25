from odoo import models, api, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

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

    quantity_requested = fields.Float(related='move_ids_without_package.product_uom_qty')

    packing_list_ids = fields.One2many(
        'stock.production.lot.serial',
        compute='_compute_packing_list_ids'
    )

    product_search_id = fields.Many2one('product.product')

    potential_lot_serial_ids = fields.One2many(
        'stock.production.lot.serial',
        'potential_picking_id',
        'Stock Disponibles'
    )

    @api.multi
    def _compute_packing_list_ids(self):
        for item in self:
            production = self.env['mrp.production'].search([('stock_picking_id', '=', item.id)])
            if production:
                lot_ids = production.mapped('workorder_ids').mapped('production_finished_move_line_ids').mapped('lot_id')
                item.packing_list_ids = lot_ids.filtered(
                    lambda a: a.product_id in item.move_ids_without_package.mapped('product_id')
                ).mapped('stock_production_lot_serial_ids')

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
