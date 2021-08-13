# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class AccountInvoiceRefund(models.TransientModel):
    """Refunds invoice"""

    _name = "pos.order.refund"
    _description  = 'Notas de Credito POS' 

    tipo_nota = fields.Many2one(
            'sii.document_class',
            string="Tipo De nota",
            required=True,
            domain=[('document_type','in',['debit_note','credit_note']), ('dte','=',True)],
        )
    filter_refund = fields.Selection(
            [
                ('1','Anula Documento de Referencia'),
                ('2','Corrige texto Documento Referencia'),
                ('3','Corrige montos'),
            ],
            default='3',
            string='Refund Method',
            required=True, help='Refund base on this type. You can not Modify and Cancel if the invoice is already reconciled',
        )
    motivo = fields.Char("Motivo")
    date_order = fields.Date(string="Fecha de Documento", default=lambda self: fields.Date.context_today(self))
    session_id = fields.Many2one('pos.session', u'Caja')
    
    @api.model
    def default_get(self, fields_list):
        values = super(AccountInvoiceRefund, self).default_get(fields_list)
        if 'tipo_nota' in fields_list:
            tipo_nota_recs = self.env['sii.document_class'].search([('document_type','in',['credit_note']), ('dte','=',True)], limit=1)
            if tipo_nota_recs:
                values['tipo_nota'] = tipo_nota_recs.id
        return values

    @api.multi
    def confirm(self):
        """Create a copy of order  for refund order"""
        PosOrder = self.env['pos.order']
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for order in self.env['pos.order'].browse(active_ids):
            order_vals = order._prepare_refund(self.session_id)
            order_vals['referencias'] = [[5,], [0, 0, {
                'origen': int(order.sii_document_number),
                'sii_referencia_TpoDocRef': order.document_class_id.id,
                'sii_referencia_CodRef': self.filter_refund,
                'motivo': self.motivo,
                'fecha_documento': self.date_order
            }]]
            clone = order._refund(order_vals)
            for line in order.lines:
                clone_line = line._refund(line._prepare_refund_line(clone))
            PosOrder += clone
        res = {
            'name': _('Return Products'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.order',
            'res_id': PosOrder.ids[0],
            'view_id': False,
            'context': context,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
        return res
