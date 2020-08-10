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

    is_balance = fields.Boolean('Es Balance')

    breakdown_balance_ids = fields.Many2many('account.move.line', compute='compute_breakdown')

    usd_value_in_clp = fields.Float('Valor del Dolar')

    @api.multi
    def get_balance_clp(self):
        for item in self:
            accounts = self.env['account.account'].search([('company_id', '=', self.env.user.company_id.id)])
            date = datetime.date.today()
            account_invoice = self.env['account.invoice'].search([('account_id', 'in', accounts.mapped('id'))])

            for ac in accounts:
                ac_move_line = self.env['account.move.line'].search([('account_id', '=', ac.id)])
                invoices = self.env['account.invoice'].search([('account_id','=',ac.id)])
                debit = []
                credit = []
                for inv in invoices:
                    d = ac_move_line.filtered(lambda a: a.invoice_id.id == inv.id).mapped('debit')
                    models._logger.error(d)
                    c = ac_move_line.filtered(lambda a: a.invoice_id.id == inv.id).mapped('credit')
                    models._logger.error(c)
                    debit.append(d)
                    credit.append(c)
                balance = self.env['balance.sheet.clp'].search([('account_id', '=', ac.id)])
                if balance:
                    if len(balance) == 2:
                            balance[-1].unlink()
                    else:
                        balance.write({
                            'balance': debit - credit
                        })
                else:
                    self.env['balance.sheet.clp'].create({
                        'account_id': ac.id,
                        'account_type': ac.user_type_id.id,
                        'balance': sum(debit) - sum(credit),
                        'is_balance': True
                    })

    @api.multi
    @api.depends('account_id')
    def compute_breakdown(self):
        for item in self:
            item.breakdown_balance_ids = self.env['account.move.line'].search([('account_id', '=', item.account_id.id)])

    @api.multi
    def go_to_breakdown(self):
        for item in self:
            return {
                'name': "Desglose",
                'view_type': 'form',
                'view_mode': 'tree,graph,form,pivot',
                'res_model': 'account.move.line',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'views': [
                    [self.env.ref('account.view_move_line_tree').id,
                     'tree']],
                'domain': [('id', 'in', item.breakdown_balance_ids.mapped("id"))]
            }
