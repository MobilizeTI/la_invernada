from odoo import models, fields, api
import requests
import json


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    exchange_rate = fields.Float(
        'Tasa de Cambio'
    )

    @api.model
    @api.onchange('date_invoice')
    def _default_exchange_rate(self):
        date = self.date_invoice
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

    def action_invoice_open(self):

        if self.id:
            if not self.exchange_rate or self.exchange_rate == 0:
                raise models.ValidationError('debe existir una taza de cambio')

        return super(AccountInvoice, self).action_invoice_open()

    @api.multi
    def compute_invoice_totals(self, company_currency, invoice_move_lines):
        total = 0
        total_currency = 0
        for line in invoice_move_lines:
            if self.currency_id != company_currency:
                currency = self.currency_id
                date = self._get_currency_rate_date() or fields.Date.context_today(self)
                if not (line.get('currency_id') and line.get('amount_currency')):
                    line['currency_id'] = currency.id
                    line['amount_currency'] = currency.round(line['price'])
                    line['price'] = currency.with_context(
                        optional_usd=self.exchange_rate
                    )._convert(line['price'], company_currency, self.company_id, date)
            else:
                line['currency_id'] = False
                line['amount_currency'] = False
                line['price'] = self.currency_id.round(line['price'])
            if self.type in ('out_invoice', 'in_refund'):
                total += line['price']
                total_currency += line['amount_currency'] or line['price']
                line['price'] = - line['price']
            else:
                total -= line['price']
                total_currency -= line['amount_currency'] or line['price']
        return total, total_currency, invoice_move_lines
