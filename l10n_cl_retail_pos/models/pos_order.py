from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class PosOrder(models.Model):
    _inherit = 'pos.order'
    
    @api.multi
    def action_force_timbre(self):
        for order in self.with_context(force_timbre=True):
            if order.sii_document_number <= 0:
                continue
            # al forzar timbre no crear creditos
            if order.state in ('paid', 'done'):
                order.do_validate()
            else:
                order.with_context(skip_partner_credit_create=True).action_pos_order_paid()
        return True
    
    def _set_fields_aditionals_invoice_line(self, line, invoice_id, inv_line):
        inv_line = super(PosOrder, self)._set_fields_aditionals_invoice_line(line, invoice_id, inv_line)
        inv_line['name'] = line.product_id.display_name
        return inv_line