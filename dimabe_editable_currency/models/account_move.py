from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    exchange_rate = fields.Float(
        'Tasa de Cambio'
    )


    def action_post(self):

        if self.id:
            if not self.exchange_rate or self.exchange_rate == 0:
                raise models.ValidationError('debe existir una taza de cambio')

        return super(AccountMove, self).action_post()

    @api.model
    @api.onchange('date')
    def _default_exchange_rate(self):
        date = self.date
        if date:
            currency_id = self.env['res.currency'].search([('name', '=', 'USD')])
            rates = currency_id.rate_ids.search([('name', '=', date)])
            if len(rates) == 0:
                currency_id.get_rate_by_date(date)

            rates = self.env['res.currency.rate'].search([('name', '<=', date)])

            if len(rates) > 0:
                rate = rates[0]
                self.exchange_rate = 1 / rate.rate
        else:
            self.exchange_rate = 0

    @api.onchange('exchange_rate')
    def _onchange_date(self):
        '''On the form view, a change on the exchange rate will trigger onchange() on account.move
        but not on account.move.line even the date field is related to account.move.
        Then, trigger the _onchange_amount_currency manually.
        '''
        self.line_ids._onchange_amount_currency()
    
    