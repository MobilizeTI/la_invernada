from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _

from odoo.tools.float_utils import float_is_zero


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'
    
    @api.model
    def default_get(self, fields_list):
        values = super(StockReturnPicking, self).default_get(fields_list)
        picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
        if picking.transfer_requisition_id:
            values['original_location_id'] = picking.transfer_requisition_id.location_id.id
            values['location_id'] = picking.transfer_requisition_id.location_id.id
            if picking.transfer_requisition_id.picking_ids:
                values['picking_id'] = picking.transfer_requisition_id.picking_ids[0].id
        return values
    
    def _prepare_move_default_values(self, return_line, new_picking):
        vals = super(StockReturnPicking, self)._prepare_move_default_values(return_line, new_picking)
        # cuando es un picking de una transferencia, al estar en este asistente pasar la transferencia en el campo de devolucion
        if new_picking.transfer_requisition_devolution_id and return_line.move_id.transfer_requisition_line_dispatch_id:
            vals['transfer_requisition_line_dispatch_id'] = False
            vals['transfer_requisition_line_return_id'] = return_line.move_id.transfer_requisition_line_dispatch_id.id
        # cuando es un picking de una transferencia, al estar en este asistente pasar la transferencia en el campo de devolucion
        if new_picking.transfer_requisition_id and return_line.move_id.transfer_requisition_line_id:
            vals['transfer_requisition_line_id'] = False
            vals['transfer_requisition_line_return_id'] = return_line.move_id.transfer_requisition_line_id.id
        return vals
    
    def _prepare_picking_default_values(self, picking_type_id):
        vals = super(StockReturnPicking, self)._prepare_picking_default_values(picking_type_id)
        # cuando es un picking de una transferencia, al estar en este asistente pasar la transferencia en el campo de devolucion
        if self.picking_id.transfer_requisition_dispatch_id:
            vals['transfer_requisition_dispatch_id'] = False
            vals['transfer_requisition_devolution_id'] = self.picking_id.transfer_requisition_dispatch_id.id
        if self.picking_id.transfer_requisition_id:
            vals['transfer_requisition_id'] = False
            vals['transfer_requisition_devolution_id'] = self.picking_id.transfer_requisition_id.id
        return vals
