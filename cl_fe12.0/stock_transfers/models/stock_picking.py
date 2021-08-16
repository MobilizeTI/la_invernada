from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    transfer_requisition_dispatch_id = fields.Many2one('transfer.requisition', u'Transferencia(despacho)', ondelete='restrict')
    transfer_requisition_devolution_id = fields.Many2one('transfer.requisition', u'Transferencia(Devolucion)', ondelete='restrict')
    transfer_requisition_id = fields.Many2one('transfer.requisition', u'Transferencia(recepcion)', ondelete='restrict')
    
    @api.multi
    def action_cancel(self):
        for picking in self:
            if picking.transfer_requisition_id and not self.env.context.get('force_cancel_picking'):
                raise UserError(_("No se permiten cancelar recepciones de transferencias internas, debe recibir los productos y luego hacer una devolucion"))
        return super(StockPicking, self).action_cancel()