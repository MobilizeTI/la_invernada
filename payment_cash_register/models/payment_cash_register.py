# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import UserError, RedirectWarning, ValidationError

class AccountPayment(models.Model):
    _inherit = 'account.payment'
    
    @api.onchange('journal_id')
    def _onchange_journal(self):
        res = super(AccountPayment, self)._onchange_journal()
        if self.apply_cash_register and self.journal_id and self.cash_register_id:
            if self.journal_id != self.cash_register_id.journal_id:
                self.cash_register_id = False
        return res
    
    @api.multi
    def _prepare_cash_register_statement(self):
        bank_statement_vals = {
            'statement_id': self.cash_register_id.id,
            'date': self.payment_date,
            'ref': self.name,
            'partner_id': self.partner_id.id,
        }
        amount = self.amount
        if self.partner_type == 'supplier':
            amount = self.amount * -1
            bank_statement_vals['is_cash_out'] = True
        else:
            bank_statement_vals['is_cash_in'] = True
        if len(self.invoice_ids) == 1:
            #si es NC el valor deberia ser negativo
            if self.invoice_ids[0].type == 'out_refund':
                amount = self.amount * -1
                bank_statement_vals.pop('is_cash_out', False)
                bank_statement_vals.pop('is_cash_in', False)
        name = self.name
        if self.communication:
            name = self.communication
        bank_statement_vals.update({
            'name': name,
            'amount': amount,
        })
        return bank_statement_vals
        
    @api.multi
    def action_create_cash_register(self):
        statement_recs = self.env['account.bank.statement.line'].browse()
        for payment in self:
            if payment.apply_cash_register and payment.cash_register_id:
                if payment.cash_register_id.state != 'open':
                    raise UserError("No puede asociar el pago a la caja: %s que ya esta cerrada, por favor verifique" % 
                                    (payment.cash_register_id.name))
                vals = payment._prepare_cash_register_statement()
                if payment.journal_id != payment.cash_register_id.journal_id:
                    raise UserError("Payment method on payment is not match with method on cash register.")
                vals['account_id'] = payment.journal_id.default_debit_account_id.id
                statement_line = self.env['account.bank.statement.line'].create(vals)
                statement_recs |= statement_line
                if payment.move_line_ids:
                    payment.move_line_ids.write({
                        'statement_line_id': statement_line.id,
                        'statement_id': payment.cash_register_id.id,
                    })
        return statement_recs
    
    @api.multi
    def post(self):
        res = super(AccountPayment, self).post()
        self.action_create_cash_register()
        return res
    
    @api.multi
    def cancel(self):
        statement_line_recs = self.env['account.bank.statement.line'].browse()
        for payment in self:
            if payment.cash_register_id:
                #si la caja esta cerrada, no permitir cancelar el pago
                #se deberia reabrir la caja de ser necesario
                if payment.cash_register_id.state != 'open' and not self.env.context.get('force_cancel_register'):
                    raise UserError("No puede cancelar este pago ya que la caja asociada: %s esta cerrada, por favor verifique." % 
                                    (payment.cash_register_id.name))
                #eliminar la linea de pago que se creo en la caja registradora
                statement_line_recs |= payment.move_line_ids.mapped('statement_line_id')
        res = super(AccountPayment, self).cancel()
        if statement_line_recs:
            statement_line_recs.unlink()
        return res

    apply_cash_register = fields.Boolean(string="Add Cash Register Entry")
    cash_register_id = fields.Many2one('account.bank.statement', string="Cash Register")

