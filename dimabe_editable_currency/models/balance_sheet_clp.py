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
                balance = self.env['balance.sheet.clp'].search([('account_id.id', '=', ac.id)])
                date = datetime.date.today()
                res = requests.request(
                    'GET',
                    'https://services.dimabe.cl/api/currencies?date={}'.format(date.strftime('%Y-%m-%d')),
                    headers={
                        'apikey': '790AEC76-9D15-4ABF-9709-E0E3DC45ABBC'
                    }
                )
                ac_move_line = self.env['account.move.line'].search([('account_id', '=', ac.id)])
                debit = sum(ac_move_line.mapped('debit'))
                credit = sum(ac_move_line.mapped('credit'))
                response = json.loads(res.text)
                if res.status_code == 200:
                    for data in response:
                        if data['currency'] == 'USD':
                            usd = data['value'].replace(',', '.')

                    tmp = (debit - credit) * float(usd)
                    if not balance:
                        self.env['balance.sheet.clp'].create({
                            'account_id': ac.id,
                            'account_type': ac.user_type_id.id,
                            'balance': tmp
                        })
                    else:
                        balance.write({
                            'account_type': ac.user_type_id.id,
                            'balance': tmp
                        })

