from odoo import models, api, fields, tools

class PosSession(models.Model):
    _inherit = 'pos.session'
    
    enable_cash_in_out = fields.Boolean("Habilitar Ingresar/Sacar Dinero", related='config_id.enable_cash_in_out')
    
    @api.multi
    def action_create_cash_operation(self, cashier_id, vals, cash_type):
        cash_model = 'cash.box.in'
        if cash_type == "take_money":
            cash_model = 'cash.box.out'
        Cash = self.env[cash_model]
        ctx = self.env.context.copy()
        ctx['active_model'] = self._name
        ctx['active_ids'] = self.ids
        ctx['active_id'] = self.ids[0] if self.ids else False
        new_cash = Cash.with_context(ctx).sudo(cashier_id).create(vals)
        return new_cash.run()