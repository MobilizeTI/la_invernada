
from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    @api.model
    def _prepare_picking_from_pos(self, partner, pos_config, location, location_dest):
        picking_vals = {
            'partner_id': partner.id,
            'picking_type_id': location.main_warehouse_id.out_type_id.id,
            'location_id': location.id,
            'location_dest_id': location_dest.id,
        }
        return picking_vals
    
    @api.model
    def _create_picking_from_pos(self, partner, pos_config, location, location_dest, picking_values):
        picking_vals = self._prepare_picking_from_pos(partner, pos_config, location, location_dest)
        picking_vals.update(picking_values)
        new_picking = self.create(picking_vals)
        new_picking.onchange_picking_type()
        new_picking.write(picking_values)
        return new_picking
    
    @api.model
    def _prepate_move_vals_from_pos(self, pos_line_vals, picking, location, location_dest):
        product_model = self.env['product.product']
        product = product_model.browse(pos_line_vals['product_id'])
        move_vals = {
            'picking_id': picking.id,
            'product_id': product.id,
            'name': product.display_name,
            'product_uom_qty': pos_line_vals['qty'],
            'product_uom': product.uom_id.id,
            'location_id': location.id,
            'location_dest_id': location_dest.id,
        }
        return move_vals
    
    @api.model
    def _create_stock_move_from_pos(self, pos_line_vals, picking, location, location_dest):
        stock_model = self.env['stock.move']
        move_vals = self._prepate_move_vals_from_pos(pos_line_vals, picking, location, location_dest)
        new_move = stock_model.create(move_vals)
        new_move.onchange_product_id()
        return new_move
    
    @api.model
    def create_picking_from_ui(self, orderline, partner_id, pos_config_id, picking_values=None):
        if picking_values is None:
            picking_values = {}
        pos_config_model = self.env['pos.config']
        partner_model = self.env['res.partner']
        if partner_id and pos_config_id:
            customer_id = int(partner_id)
            pos_config_id = int(pos_config_id)
            pos_config = pos_config_model.browse(pos_config_id)
            partner = partner_model.browse(customer_id)
            location = pos_config.stock_location_id
            location_dest = partner.property_stock_customer
            new_picking = self._create_picking_from_pos(partner, pos_config, location, location_dest, picking_values)
            #create move lines
            for line in orderline:
                new_move = self._create_stock_move_from_pos(line, new_picking, location, location_dest)
        return (new_picking.id, new_picking.display_name)
