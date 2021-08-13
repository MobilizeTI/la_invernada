from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class StockMove(models.Model):

    _inherit = 'stock.move'
    
    transfer_requisition_line_id = fields.Many2one('transfer.requisition.line', u'Detalle de Transferencia(recepcion)')
    transfer_requisition_line_dispatch_id = fields.Many2one('transfer.requisition.line', u'Detalle de Transferencia(despacho)')
    transfer_requisition_line_return_id = fields.Many2one('transfer.requisition.line', u'Detalle de Transferencia(devolucion)')
            
    # @override
    @api.multi
    def _action_done(self):
        """Call _account_entry_move for internal moves as well."""
        # cuando este activo que cree asiento contable de transferencias en la company
        # pasar contexto en llamada super
        if self.env.user.company_id.transfer_create_account_move:
            return super(StockMove, self.with_context(force_transfer_create_account_move=True))._action_done()
        return super(StockMove, self)._action_done()
