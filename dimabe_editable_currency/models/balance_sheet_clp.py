from odoo import fields, models, api


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

    # @api.multi
    # def get_data(self):
    #     for item in self:
    #         raise models.UserError('Hola')
    #         accounts = self.env['account.account'].search([('company_id', '=', self.env.user.company_id.id)])
    #         for ac in accounts:
    #             ac_move_line = self.env['account.move.line'].search([('account_id.id', '=', ac.id)])
    #
    #             balance = self.env['balance.sheet.clp'].search([('account_id.id', '=', ac.id)])
    #             if not balance:
    #                 debit = sum(ac_move_line.mapped('debit'))
    #                 credit = sum(ac_move_line.mapped('credit'))
    #                 if ac_move_line:
    #
    #                     self.env['balance.sheet.clp'].create({
    #                         'account_id': ac.id,
    #                         'from': ac_move_line[0].create_date,
    #                         'to': ac_move_line[-1].create_date,
    #                         'account_type': ac.user_type_id.id,
    #                         'balance': debit - credit
    #                     })
    #                 else:
    #                     self.env['balance.sheet.clp'].create({
    #                         'account_id': ac.id,
    #                         'account_type': ac.user_type_id.id,
    #                         'balance': debit - credit
    #                     })
    #             else:
    #                 balance.write({
    #                     'from': ac_move_line[0].create_date,
    #                     'to': ac_move_line[-1].create_date,
    #                     'account_type': ac.user_type_id.id,
    #                     'balance': debit - credit
    #                 })
    #     return {
    #         'name': "Balance",
    #         'view_type': 'form',
    #         'view_mode': 'tree,graph,form,pivot',
    #         'res_model': 'balance.sheet.clp',
    #         'view_id': False,
    #         'type': 'ir.actions.act_window',
    #         'views': [
    #             [self.env.ref('dimabe_editable_currency.balance_sheet_clp_view_tree').id, 'tree']],
    #     }
