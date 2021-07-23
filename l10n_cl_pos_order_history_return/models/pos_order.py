from odoo import models, api, fields, tools
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _


class PosOrder(models.Model):
    _inherit = 'pos.order'
    
    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        return_data_aditional = ui_order.get('return_data_aditional')
        # return_data_aditional es un diccionario creado en JS con valores adicionales a pasar al backend
        # solo tomar los campos que existan en pos.order para evitar procesar campos que no existan
        # pasar las referencias a la NC en base al pedido original
        if ui_order.get('origin_order_id') and return_data_aditional:
            origin_order = self.browse(ui_order['origin_order_id'])
            order_fields['referencias'] = [(0, 0, {
                'origen': int(origin_order.sii_document_number),
                'sii_referencia_TpoDocRef': origin_order.document_class_id.id,
                'sii_referencia_CodRef': return_data_aditional.get('filter_refund') or '1',
                'motivo': return_data_aditional.get('note') or '',
                'fecha_documento': fields.Date.context_today(self, fields.Datetime.from_string(origin_order.date_order)),
            })]
        return order_fields