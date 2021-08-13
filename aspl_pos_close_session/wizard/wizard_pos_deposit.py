from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare


class WizardPosDeposit(models.TransientModel):
    _name = 'wizard.pos.deposit'
    _description = 'Asistente para depositar pagos del POS'

    session_id = fields.Many2one('pos.session', 'Sesion', 
        readonly=True)
    partner_company_id = fields.Many2one('res.partner', 'Empresa de compañia')
    currency_id = fields.Many2one('res.currency', string='Currency', 
        default=lambda self: self.env.user.company_id.currency_id)
    cash_register_id = fields.Many2one('account.bank.statement', string="Registro de Caja")
    journal_dest_id = fields.Many2one('account.journal', 'Cuenta Bancaria')
    amount_cash = fields.Monetary(u'Efectivo a Depositar')
    deposit_date = fields.Date('Fecha de Deposito', 
        default=lambda self: fields.Date.context_today(self))
    papeleta_number = fields.Char('Numero de papeleta', size=256)
            
    @api.model
    def default_get(self, fields_list):
        values = super(WizardPosDeposit, self).default_get(fields_list)
        session_model = self.env['pos.session']
        active_ids = self.env.context.get('active_ids', [])
        if 'session_id' in fields_list:
            session = session_model.browse(active_ids[0])
            values['partner_company_id'] = self.env.user.company_id.partner_id.id
            values['session_id'] = session.id
            values['cash_register_id'] = session.cash_register_id.id
        return values
    
    def _prepare_deposit_values(self):
        return {
            'session_id': self.session_id.id,
            'pos_config_id': self.session_id.config_id.id,
            'warehouse_id': self.session_id.config_id.stock_location_id.main_warehouse_id.id,
            'cash_register_id': self.cash_register_id.id,
            'journal_dest_id': self.journal_dest_id.id,
            'amount_cash': self.amount_cash,
            'deposit_date': self.deposit_date,
            'papeleta_number': self.papeleta_number,
        }
        
    @api.multi
    def _action_deposit(self):
        self.ensure_one()
        deposit_model = self.env['pos.deposit']
        if self.amount_cash <= 0:
            raise UserError("Por favor especifique una cantidad mayor a cero para enviar a depositar")
        if float_compare(self.amount_cash, self.session_id.cash_register_balance_end, precision_digits=self.currency_id.decimal_places) > 0:
            raise UserError("El monto de efectivo a depositar: %s no puede ser mayor al total disponible: %s, por favor verifique." % (self.amount_cash, self.session_id.cash_register_balance_end))
        new_deposit = deposit_model.create(self._prepare_deposit_values())
        new_deposit.action_sent()
        return new_deposit
    
    @api.multi
    def action_deposit(self):
        util_model = self.env['odoo.utils']
        new_deposit = self._action_deposit()
        return util_model.show_action('aspl_pos_close_session.pos_deposit_action', [('id','=',new_deposit.id)])
    
    @api.model
    def action_deposit_from_pos(self, pos_session_id, values):
        ctx = self.env.context.copy()
        ctx.update({
            'active_ids': [pos_session_id],
            'active_id': pos_session_id,
            'active_model': 'pos.session',
        })
        new_wizard_deposit = self.with_context(ctx).create(values)
        new_deposit = new_wizard_deposit._action_deposit()
        return new_deposit.read(fields=['name'])[0]
