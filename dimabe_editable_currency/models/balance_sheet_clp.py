from odoo import fields, models, api
import requests
import json
import datetime


class ModelName(models.Model):
    _name = 'balance.sheet.clp'
    _description = 'Balance de Situacion CLP'

    currency_id = fields.Many2one('res.currency', 'Moneda',
                                  default=lambda self: self.env['res.currency'].search([('name', '=', 'CLP')]))

    account_id = fields.Many2one('account.account', 'Cuenta')

    balance = fields.Monetary('Balance')

    account_type = fields.Many2one('account.account.type')

    account_from_date = fields.Datetime('Desde')

    account_to_date = fields.Datetime('Hasta')

    @api.multi
    def get_data(self):
        for item in self:
            accounts = self.env['account.account'].search([('company_id', '=', self.env.user.company_id.id)])
            for ac in accounts:
                ac_move_line = self.env['account.move.line'].search([('account_id.id', '=', ac.id)])
                balance = self.env['balance.sheet.clp'].search([('account_id.id', '=', ac.id)])
                if not balance:
                    debit = sum(ac_move_line.mapped('debit'))
                    credit = sum(ac_move_line.mapped('credit'))
                    balance_total = debit - credit
                    balance_clp = self.get_balance_in_clp(balance_total)
                    if ac_move_line:
                        self.env['balance.sheet.clp'].create({
                            'account_id': ac.id,
                            'account_type': ac.user_type_id.id,
                            'balance': balance_clp
                        })
                else:
                    balance.write({
                        'from': ac_move_line[0].create_date,
                        'to': ac_move_line[-1].create_date,
                        'account_type': ac.user_type_id.id,
                        'balance': balance_clp
                    })

    def get_balance_in_clp(self, balance):
        for item in self:
            date = datetime.date.today()
            res = requests.request(
                'GET',
                'https://services.dimabe.cl/api/currencies?date={}'.format(date.strftime('%Y-%m-%d')),
                headers={
                    'apikey': '790AEC76-9D15-4ABF-9709-E0E3DC45ABBC'
                }
            )

            response = json.loads(res.text)

            for data in response:
                if data['currency'] == 'USD':
                    usd = data['value'].replace(',', '.')

            tmp = balance * float(usd)
            return tmp
