# -*- coding: utf-8 -*-

import pytz
import time
from datetime import datetime
from collections import OrderedDict

from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF, DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.exceptions import UserError, ValidationError

class PosOrderRefund(models.TransientModel):

    _inherit = 'pos.order.refund'
    
    line_ids = fields.One2many('pos.order.refund.line', 'wizard_id', u'Productos a devolver', required=False, help=u"",)
    note_id = fields.Many2one('pos.order.reason.nc', u'Motivo')
    
    @api.onchange('note_id',)
    def onchange_note_id(self):
        self.motivo = self.note_id.name or ''
    
    @api.model
    def default_get(self, fields_list):
        values = super(PosOrderRefund, self).default_get(fields_list)
        if 'line_ids' in fields_list:
            default_line =  {
                'product_id': False,
                'line_origin_id': False,
                'qty': 0,
                'max_qty': 0,
            }
            order = self.env['pos.order'].browse(self.env.context['active_ids'][0])
            line_ids = []
            lines_data = OrderedDict()
            for line in order.lines:
                #los cambios no considerarlos
                #las cantidades se restaran del nuevo modelo de cambios ya que ahi tengo a que linea pertenece cada cambio
                if line.qty < 0.0:
                    continue
                lines_data.setdefault(line.id, default_line.copy())
                lines_data[line.id]['qty'] += line.qty
                lines_data[line.id]['max_qty'] += line.qty
                lines_data[line.id]['product_id'] = line.product_id.id
                lines_data[line.id]['line_origin_id'] = line.id
            SQL = """
                SELECT SUM(l.qty) AS qty, l.line_origin_id, l.product_id
                    FROM pos_order_line l
                        INNER JOIN pos_order p ON p.id = l.order_id
                    WHERE p.origin_order_id = %(origin_order_id)s
                        AND line_origin_id IS NOT NULL
                    GROUP BY l.line_origin_id, l.product_id
                """
            self.env.cr.execute(SQL, {'origin_order_id': order.id})
            for devolution in self.env.cr.dictfetchall():
                lines_data.setdefault(devolution['line_origin_id'], default_line.copy())
                lines_data[devolution['line_origin_id']]['qty'] += devolution['qty']
                lines_data[devolution['line_origin_id']]['max_qty'] += devolution['qty']
                lines_data[devolution['line_origin_id']]['product_id'] = devolution['product_id']
                lines_data[devolution['line_origin_id']]['line_origin_id'] = devolution['line_origin_id']
            for devolution_line in lines_data.values():
                if devolution_line['qty'] <= 0.0:
                    continue
                line_ids.append((0, 0, devolution_line))
            if not line_ids:
                raise UserError(u"No hay productos que devolver, por favor verifique.")
            values['line_ids'] = line_ids
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
            for line in self.line_ids.filtered('line_origin_id'):
                line_vals = line.line_origin_id._prepare_refund_line(clone)
                line_vals['qty'] = -line.qty
                clone_line = line.line_origin_id._refund(line_vals)
                clone_line._onchange_amount_line_all()
            clone._onchange_amount_all()
            clone.compute_taxes()
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

    
class PosOrderRefundLine(models.TransientModel):

    _name = 'pos.order.refund.line'
    _description = u'pos.order.refund.line'
    
    wizard_id = fields.Many2one('pos.order.refund', u'Asistente', required=False, help=u"",)
    product_id = fields.Many2one('product.product', string=u'Producto')
    qty = fields.Float(u'Cantidad', digits=dp.get_precision('Product Unit of Measure'), default=1)
    max_qty = fields.Float(u'Cantidad maxima permitida', digits=dp.get_precision('Product Unit of Measure'))
    line_origin_id = fields.Many2one('pos.order.line', u'Linea Original', required=False, help=u"",)
    
    @api.one
    @api.constrains('qty', 'max_qty')
    def check_qty(self):
        if self.qty <= 0:
            raise ValidationError(u"La cantidad a devolver debe ser mayor a cero, por favor verifique la linea con el producto: %s" %
                                  self.product_id.display_name)
        if self.qty > self.max_qty:
            raise ValidationError(u"La cantidad a devolver: %s no puede ser mayor a la cantidad maxima permitida: %s por favor verifique la linea con el producto: %s" %
                                  (self.qty, self.max_qty, self.product_id.display_name))
            
    @api.onchange('qty', 'max_qty')
    def _onchange_qty(self):
        if self.qty <= 0:
            return {'warning': {'title': u'Informacion para el usuario',
                                'message': u"La cantidad a devolver debe ser mayor a cero, por favor verifique la linea con el producto: %s" %
                                            self.product_id.display_name 
                                }
                    }
        if self.qty > self.max_qty:
            self.qty = self.max_qty
            return {'warning': {'title': u'Informacion para el usuario',
                                'message': u"La cantidad a devolver: %s no puede ser mayor a la cantidad maxima permitida: %s por favor verifique la linea con el producto: %s" %
                                            (self.qty, self.max_qty, self.product_id.display_name)
                                }
                    }
        
        