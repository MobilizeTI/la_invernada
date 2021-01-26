from odoo import models, fields, api

class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'
    
    def _compute_amount_fields(self, amount, src_currency, company_currency):
        """ Helper function to compute value for fields debit/credit/amount_currency based on an amount and the currencies given in parameter"""

        optional_usd = self.env.context.get('optional_usd') or False
        amount_currency = False
        currency_id = False
        date = self.env.context.get('date') or fields.Date.today()
        company = self.env.context.get('company_id')
        company = self.env['res.company'].browse(company) if company else self.env.user.company_id
        if src_currency and src_currency != company_currency:
            amount_currency = amount
            amount = src_currency.with_context(
                optional_usd=optional_usd
            )._convert(amount, company_currency, company, date)
            currency_id = src_currency.id
        debit = amount > 0 and amount or 0.0
        credit = amount < 0 and -amount or 0.0
        return debit, credit, amount_currency, currency_id

    @api.onchange('amount_currency', 'currency_id')
    def _onchange_amount_currency(self):
        '''Recompute the debit/credit based on amount_currency/currency_id and date.
        However, date is a related field on account.move. Then, this onchange will not be triggered
        by the form view by changing the date on the account.move.
        To fix this problem, see _onchange_date method on account.move.
        '''
        for line in self:
            amount = line.amount_currency
            if line.currency_id and line.currency_id != line.company_currency_id:
                amount = line.currency_id.with_context(optional_usd=self.move_id.exchange_rate).compute(amount,
                                                                                                        line.company_currency_id)
                line.debit = amount > 0 and amount or 0.0
                line.credit = amount < 0 and -amount or 0.0

    @api.multi
    def test(self):
        for item in self:
            accounts = self.env['account.account'].search([('company_id', '=', self.env.user.company_id.id)])
            for ac in accounts:
                ac_move_line = self.env['account.move.line'].search([('account_id.id', '=', ac.id)])

                balance = self.env['balance.sheet.clp'].search([('account_id.id', '=', ac.id)])
                if not balance:
                    debit = sum(ac_move_line.mapped('debit'))
                    credit = sum(ac_move_line.mapped('credit'))
                    if ac_move_line:

                        self.env['balance.sheet.clp'].create({
                            'account_id': ac.id,
                            'from': ac_move_line[0].create_date,
                            'to': ac_move_line[-1].create_date,
                            'account_type': ac.user_type_id.id,
                            'balance': debit - credit
                        })
                    else:
                        self.env['balance.sheet.clp'].create({
                            'account_id': ac.id,
                            'account_type': ac.user_type_id.id,
                            'balance': debit - credit
                        })
                else:
                    balance.write({
                        'from': ac_move_line[0].create_date,
                        'to': ac_move_line[-1].create_date,
                        'account_type': ac.user_type_id.id,
                        'balance': debit - credit
                    })

            return {
                'name': "Balance",
                'view_type': 'tree',
                'view_mode': 'tree,graph,form,pivot',
                'res_model': 'balance.sheet.clp',
                'view_id': self.env.ref('dimabe_editable_currency.balance_sheet_clp_view_tree').id,
                'type': 'ir.actions.act_window',
                'views': [
                    [self.env.ref('dimabe_editable_currency.balance_sheet_clp_view_tree').id, 'tree']],
            }
