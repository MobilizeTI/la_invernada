from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class AccountPayment(models.Model):
    _inherit = 'account.payment'
    
    @api.multi
    def _prepare_cash_register_statement(self):
        vals = super(AccountPayment, self)._prepare_cash_register_statement()
        if len(self.invoice_ids) == 1:
            #si es NC el valor deberia ser negativo
            if self.invoice_ids[0].type == 'out_refund':
                vals['force_is_credit_note'] = True
        return vals