from odoo import models, api, fields, tools


class AccountCashStatement(models.Model):
    _inherit = 'account.bank.statement'

    @api.depends('line_ids', 'line_ids.amount')
    def _compute_total_entry_custom(self):
        for bank_statement in self:
            total_entry, total_entry_encoding_deposit, total_entry_in, total_entry_out, total_entry_cn, total_entry_encoding_adjustment = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
            payment_count = 0
            for line in bank_statement.line_ids:
                if line.pos_deposit_id:
                    total_entry_encoding_deposit += line.amount
                elif line.is_adjustment:
                    total_entry_encoding_adjustment += line.amount
                elif line._is_credit_note():
                    total_entry_cn += line.amount
                elif line.is_cash_in:
                    total_entry_in += line.amount
                elif line.is_cash_out:
                    total_entry_out += line.amount
                else:
                    total_entry += line.amount
                    # no considerar los vueltos o cambios como pagos
                    if line.amount > 0:
                        payment_count += 1
            bank_statement.total_entry_encoding_custom = total_entry
            bank_statement.total_entry_encoding_put_in = total_entry_in
            bank_statement.total_entry_encoding_take_out = total_entry_out
            bank_statement.total_entry_encoding_deposit = total_entry_encoding_deposit
            bank_statement.total_entry_encoding_adjustment = total_entry_encoding_adjustment
            bank_statement.total_entry_encoding_cn = total_entry_cn
            bank_statement.payment_count = payment_count

    total_entry_encoding_custom = fields.Monetary('Total Transactions', 
        compute='_compute_total_entry_custom', store=True)
    total_entry_encoding_put_in = fields.Monetary('Cash put in', 
        compute='_compute_total_entry_custom', store=True)
    total_entry_encoding_take_out = fields.Monetary('Cash take out', 
        compute='_compute_total_entry_custom', store=True)
    total_entry_encoding_deposit = fields.Monetary('Deposit', 
        compute='_compute_total_entry_custom', store=True)
    total_entry_encoding_cn = fields.Monetary('Total Notas de credito', 
        compute='_compute_total_entry_custom', store=True)
    total_entry_encoding_adjustment = fields.Monetary('Total Ajustes de cierre', 
        compute='_compute_total_entry_custom', store=True)
    payment_count = fields.Integer('Cantidad de Pagos', 
        compute='_compute_total_entry_custom', store=True)
    
    @api.multi
    def _prepare_statement_for_difference(self, account, name):
        vals = super(AccountCashStatement, self)._prepare_statement_for_difference(account, name)
        vals['is_adjustment'] = True
        return vals


class AccountBankStatementLine(models.Model):    
    _inherit = "account.bank.statement.line"
    
    is_cash_in = fields.Boolean('Cash In?', readonly=False, default=False, copy=False)
    is_cash_out = fields.Boolean('Cash Out?', readonly=False, default=False, copy=False)
    is_adjustment = fields.Boolean('Is adjustment?', readonly=False, default=False, copy=False)
    force_is_credit_note = fields.Boolean(u'Es Nota de Credito?', copy=False)
    pos_deposit_id = fields.Many2one('pos.deposit', 'Deposito del POS')

    @api.multi
    def _is_credit_note(self):
        is_credit_note = False
        if self.amount < 0 and self.pos_statement_id and self.pos_statement_id.amount_total < 0.0:
            is_credit_note = True
        if self.force_is_credit_note:
            is_credit_note = True
        return is_credit_note
