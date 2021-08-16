from collections import OrderedDict

from odoo import models, api, fields

class TransferRequisition(models.Model):
    _inherit = 'transfer.requisition'
    
    @api.model
    def _find_transfer_from_pos(self, transfer_id):
        return self.search([('id', '=', transfer_id)], limit=1)
    
    @api.multi
    def _find_transfer_line_from_pos(self, product, vals_line_pos):
        """
        Buscar y devolver la primera linea de la transferencia que tenga el mismo producto del pos
        """
        return self.line_ids.filtered(lambda x: x.product_id == product)

    @api.multi
    def _prepare_transfer_line_from_pos(self, product, vals_line_pos):
        line_vals = {
            'requisition_id': self.id,
            'product_id': product.id,
            'product_qty': vals_line_pos.get('qty') or 0,
        }
        return line_vals
    
    @api.multi
    def _create_transfer_line_from_pos(self, product, vals_line):
        transfer_line_model = self.env['transfer.requisition.line']
        line_rec = transfer_line_model.new(vals_line)
        line_rec.onchange_product_id()
        line_vals = transfer_line_model._convert_to_write({name: line_rec[name] for name in line_rec._cache})
        return transfer_line_model.create(line_vals)
        
    @api.model
    def set_internal_transfer_from_ui(self, transfer_id, transfer_lines):
        product_model = self.env['product.product']
        transfer = self._find_transfer_from_pos(transfer_id)
        #borrar las lineas existentes en caso de existir
        if transfer.line_ids:
            transfer.line_ids.sudo().unlink()
        real_inventory_lines = OrderedDict()
        line_key = False
        for line in transfer_lines:
            line_key = (line.get('product_id'),)
            if line_key in real_inventory_lines:
                real_inventory_lines[line_key]['qty'] += line.get('qty') or 0
            else:
                real_inventory_lines[line_key] = line.copy()
        line_vals = {}
        for line in real_inventory_lines.values():
            product = product_model.browse(line['product_id'])
            line_vals = transfer._prepare_transfer_line_from_pos(product, line)
            transfer._create_transfer_line_from_pos(product, line_vals)
        transfer.with_context(transfer_from_pos=True).action_request()
        res = {
            'model': self._name,
            'id': transfer.id,
            'name': transfer.display_name,
        }
        if self.env.user.company_id.transfer_auto_validate_picking and transfer.picking_ids:
            res = {
                'model': transfer.picking_ids[0]._name,
                'id': transfer.picking_ids[0].id,
                'name': transfer.picking_ids[0].display_name,
            }
        return res
    
    @api.model
    def received_internal_transfer_from_ui(self, transfer_id, transfer_lines):
        product_model = self.env['product.product']
        reasons = self.env['transfer.requisition.reason']
        transfer = self._find_transfer_from_pos(transfer_id)
        real_inventory_lines = OrderedDict()
        line_key = False
        for line in transfer_lines:
            line_key = (line.get('product_id'),)
            if line_key in real_inventory_lines:
                real_inventory_lines[line_key]['qty'] += line.get('qty') or 0
            else:
                real_inventory_lines[line_key] = line.copy()
        for line in real_inventory_lines.values():
            product = product_model.browse(line['product_id'])
            transfer_line = transfer._find_transfer_line_from_pos(product, line)
            if not transfer_line:
                reasons.create({
                    'name': 'Producto no esta en las lineas de transferencia',
                    'product_id': product.id,
                    'requisition_id': transfer.id,
                })
            else:
                transfer_line.write({'qty_received': line.get('qty') or 1})
        transfer._action_receive()
        return (transfer.id, transfer.display_name)
    
    @api.model
    def create(self, vals):
        new_rec = super(TransferRequisition, self).create(vals)
        self.env['pos.config'].notify_transfer_updates()
        return new_rec
    
    @api.multi
    def write(self, vals):
        res = super(TransferRequisition, self).write(vals)
        self.env['pos.config'].notify_transfer_updates()
        return res
    
    @api.multi
    def unlink(self):
        res = super(TransferRequisition, self).unlink()
        self.env['pos.config'].notify_transfer_updates()
        return res

