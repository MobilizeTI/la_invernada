from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _

from odoo.tools.float_utils import float_is_zero


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'
    
    use_documents = fields.Boolean('Generar Guia electronica?')
    is_picking_out = fields.Boolean('Picking de salida?')
    
    @api.model
    def default_get(self, fields):
        values = super(StockReturnPicking, self).default_get(fields)
        picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
        if picking:
            return_picking_type = picking.picking_type_id.return_picking_type_id or picking.picking_type_id
            if return_picking_type.code == 'outgoing':
                values['is_picking_out'] = True
                values['use_documents'] = True
        if values.get('product_return_moves'):
            product_return_moves = []
            for line in values.get('product_return_moves'):
                if not float_is_zero(line[2]['quantity'], precision_digits=0):
                    product_return_moves.append(line)
            values['product_return_moves'] = product_return_moves
        return values
    
    def _prepare_picking_default_values(self, picking_type_id):
        vals = super(StockReturnPicking, self)._prepare_picking_default_values(picking_type_id)
        vals.update({
            'use_documents': self.use_documents,
            'transport_type': '0',
            'move_reason': '7',
        })
        if self.picking_id.partner_ref:
            vals['origin'] = self.picking_id.partner_ref
        # cuando es un picking de una transferencia, al estar en este asistente pasar que no genere guia electronica
        if self.picking_id.transfer_requisition_dispatch_id or self.picking_id.transfer_requisition_id:
            vals['use_documents'] = False
        return vals

    
    @api.multi
    def _create_returns(self):
        new_picking_id, picking_type_id = super(StockReturnPicking, self)._create_returns()
        if new_picking_id:
            referencia_model = self.env['stock.picking.referencias']
            new_picking = self.env['stock.picking'].browse(new_picking_id)
            for invoice in self.picking_id.purchase_id.invoice_ids:
                if invoice.type in ('in_invoice', 'out_invoice'):
                    referencia_model.create({
                        'stock_picking_id': new_picking.id,
                        'date': invoice.date_invoice,
                        'origen': invoice.reference,
                        'sii_referencia_TpoDocRef': invoice.document_class_id.id,
                    })
        return new_picking_id, picking_type_id
