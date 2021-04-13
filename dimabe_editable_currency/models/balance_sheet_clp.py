from odoo import fields, models, api
import requests
import json
import datetime


class ModelName(models.Model):
    _name = 'balance.sheet.clp'
    _description = 'Balance de Situacion CLP'

    _sql_constraints = [
        ('account_uniq', 'UNIQUE(account_id)', 'los datos de la cuenta ya se encuentra en el sistema.')
    ]

    currency_id = fields.Many2one('res.currency', 'Moneda',
                                  default=lambda self: self.env['res.currency'].search([('name', '=', 'CLP')]))

    account_id = fields.Many2one('account.account', 'Cuenta')

    balance = fields.Monetary('Balance CLP')

    balance_usd = fields.Monetary('Balance USD')

    account_type = fields.Many2one('account.account.type')

    account_from_date = fields.Datetime('Desde')

    account_to_date = fields.Datetime('Hasta')

    is_balance = fields.Boolean('Es Balance')

    breakdown_balance_ids = fields.Many2many('account.move.line', compute='compute_breakdown')

    usd_value_in_clp = fields.Float('Valor del Dolar')

    @api.multi
    def get_balance_clp(self):
        for item in self:
            account_ids = self.env['account.account'].search([('company_id', '=', self.env.user.company_id.id)])
            usd_credit = []
            clp_credit = []
            usd_debit = []
            clp_debit = []
            for account in account_ids:
                ac_move_line = self.env['account.move.line'].search([('account_id', '=', account.id)])
                for ac_mov in ac_move_line:
                    for invoice in ac_move_line.mapped('invoice_id'):
                        if ac_mov.debit > 0:
                            usd_debit.append(ac_mov.debit)
                            clp_debit.append(invoice.amount_total)
                        if ac_mov.credit > 0:
                            usd_credit.append(ac_mov.credit)
                            clp_credit.append(invoice.amount_total)
                self.env['balance.sheet.clp'].create({
                    'account_id': account.id,
                    'balance': sum(clp_debit) - sum(clp_credit),
                    'balance_usd': sum(usd_debit) - sum(usd_credit),
                    'account_type': account.user_type_id.id,
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
