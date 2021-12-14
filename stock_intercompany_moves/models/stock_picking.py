# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, exceptions, SUPERUSER_ID
import logging
_logger = logging.getLogger('TEST ===========')


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    
    picking_transfer_id = fields.Many2one('stock.picking', 'Picking de transferencia Inter-Company')
    
    def action_view_stock(self):
        return {
            'name': 'Stock', 
            'view_type': 'form', 
            'view_mode': 'tree,form',
            'res_model': 'stock.quant', 
            'type': 'ir.actions.act_window', 
            'context': {
                'uid': 2,
                'allowed_company_ids': [], 
                'search_default_consumable': 1, 
                'default_type': 'product', 
                'active_test': False, 
                'hide_location': False, 
                'hide_lot': True, 
                'no_at_date': True, 
                'search_default_internal_loc': True, 
                'inventory_mode': True, 
                'default_product_id': self.product_id.id, 
                'single_product': True
            },
            'domain': [('product_id', 'in', self.product_id.ids), ('company_id', '!=', False)],
            'target': 'new',
        }

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    is_inter_company = fields.Boolean(related='location_dest_id.is_inter_company')
    is_inter_company_auto = fields.Boolean('Auto Validar')
    company_dest_id = fields.Many2one('res.company', 'Compañía Destino')
    do_inter_company_auto = fields.Boolean('Auto Transferir')
    
    move_transfer_count = fields.Integer(compute='_compute_move_transfer_count')
    move_transfer_ids = fields.One2many('stock.move.line', 'picking_transfer_id')
    
    @api.onchange('picking_type_id')
    def _onchange_picking_type_id_transfer(self):
        if self.picking_type_id and self.picking_type_id.company_dest_id:
            self.company_dest_id = self.picking_type_id.company_dest_id.id
            self.do_inter_company_auto = True
    
    @api.depends('move_transfer_ids')
    def _compute_move_transfer_count(self):
        for rec in self:
            rec.move_transfer_count = len(rec.move_transfer_ids)
    
    def button_validate(self):
        if self.picking_type_code == 'outgoing' and self.do_inter_company_auto and self.company_dest_id:
            SP = self.env['stock.picking'].sudo()
            SPT = self.env['stock.picking.type'].sudo().search([('code', '=', 'internal'), ('warehouse_id.company_id','=',self.company_dest_id.id)], limit=1)
            SLT = self.env['stock.location'].sudo().search([('is_inter_company', '=', True)], limit=1)
            
            items = []
            for item_line in self.move_line_ids_without_package:
                if item_line.product_id.qty_available < item_line.qty_done:
                    items.append({
                        'name': item_line.product_id.display_name,
                        'picking_type_id': SPT.id,
                        'product_id': item_line.product_id.id,
                        'product_uom_qty': item_line.qty_done - item_line.product_id.qty_available,
                        'product_uom': item_line.product_uom_id.id,
                        'location_id': SPT.default_location_src_id.id,
                        'location_dest_id': SLT.id,
                        'company_id': self.company_dest_id.id,
                    })
                    
            if items:
                picking = SP.create({
                    'picking_type_id': SPT.id,
                    'origin': self.name,
                    'location_id': SPT.default_location_src_id.id,
                    'location_dest_id': SLT.id,
                    'company_id': self.company_dest_id.id,
                    'company_dest_id': self.company_id.id,
                    'is_inter_company_auto': True,
                })
                
                for item_line in items:
                    picking.write({ 'move_ids_without_package': [(0, 0, item_line)]})
                    
                for move in picking.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
                    picking.write({
                        'move_line_ids_without_package': [(0,0, {
                            'product_id': move.product_id.id,
                            'product_uom_qty': move.product_uom_qty,
                            'product_uom_id': move.product_uom.id,
                            'qty_done': move.product_uom_qty,
                            'location_id': move.location_id.id,
                            'location_dest_id': move.location_dest_id.id,
                            'company_id': move.company_id.id
                        })]
                    })
                for move in picking.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
                    for move_line in move.move_line_ids:
                        move_line.qty_done = move_line.product_uom_qty
                picking.with_context(skip_immediate=True).button_validate()
                
                picking_transfer_id = self.env['stock.picking'].search([('origin', '=', picking.name)])
                for move_line in picking_transfer_id.move_line_ids_without_package:
                    self.write({ 'move_transfer_ids': [(4, move_line.id)] })
                
        res = super(StockPicking, self).button_validate()
        if self.picking_type_code == 'internal' and self.is_inter_company and self.company_dest_id:
            SP = self.env['stock.picking'].sudo()
            SPT = self.env['stock.picking.type'].sudo().search([('warehouse_id.company_id', '=', self.company_dest_id.id), ('code', '=', 'internal')], limit=1)
            if not SPT:
                raise exceptions.ValidationError(_('No se encontró un picking correspondiente en la compañía seleccionada'))
            
            picking = SP.create({
                'picking_type_id': SPT.id,
                'origin': self.name,
                'location_id': self.location_dest_id.id,
                'location_dest_id': SPT.default_location_dest_id.id,
                'company_id': self.company_dest_id.id
            })
            
            for item_line in self.move_line_ids_without_package:
                if item_line.qty_done:
                    picking.write({
                        'move_ids_without_package': [(0, 0, {
                            'name': item_line.product_id.display_name,
                            'picking_type_id': SPT.id,
                            'product_id': item_line.product_id.id,
                            'product_uom_qty': item_line.qty_done,
                            'product_uom': item_line.product_uom_id.id,
                            'location_id': self.location_dest_id.id,
                            'location_dest_id': SPT.default_location_dest_id.id,
                            'company_id': self.company_dest_id.id
                        })]
                    })
            
            if self.is_inter_company_auto:
                #picking.action_confirm()
                for move in picking.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
                    picking.write({
                        'move_line_ids_without_package': [(0,0, {
                            'product_id': move.product_id.id,
                            'product_uom_qty': move.product_uom_qty,
                            'product_uom_id': move.product_uom.id,
                            'qty_done': move.product_uom_qty,
                            'location_id': move.location_id.id,
                            'location_dest_id': move.location_dest_id.id,
                            'company_id': move.company_id.id
                        })]
                    })
                for move in picking.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
                    for move_line in move.move_line_ids:
                        move_line.qty_done = move_line.product_uom_qty
                picking.with_context(skip_immediate=True).button_validate()
        return res
    
    @api.model
    def fix_ir_rule(self):
        rule = self.env.ref('stock.stock_quant_rule')[0]
        rule.sudo().write({ 'perm_read': False })