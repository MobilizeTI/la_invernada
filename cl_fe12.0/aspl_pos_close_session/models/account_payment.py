from odoo import models, api, fields, tools
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'
    
    pos_deposit_id = fields.Many2one('pos.deposit', 'Deposito del POS', index=True)
    
    @api.one
    @api.depends('invoice_ids', 'payment_type', 'partner_type', 'partner_id')
    def _compute_destination_account_id(self):
        if self.pos_deposit_id:
            if not self.company_id.transfer_account_id.id:
                raise UserError(_('Transfer account not defined on the company.'))
            self.destination_account_id = self.company_id.transfer_account_id.id
        else:
            super(AccountPayment, self)._compute_destination_account_id()
            
    def _get_counterpart_move_line_vals(self, invoice=False):
        vals = super(AccountPayment, self)._get_counterpart_move_line_vals(invoice)
        #mejorar la referencia del pago en caso de ser deposito del pos
        if self.pos_deposit_id:
            vals['name'] = self.name
        return vals
    
    @api.multi
    def _prepare_cash_register_statement(self):
        vals = super(AccountPayment, self)._prepare_cash_register_statement()
        if self.pos_deposit_id:
            # el deposito debe ser negativo en el registro de caja
            vals['pos_deposit_id'] = self.pos_deposit_id.id
            vals['amount'] *= -1
        return vals
