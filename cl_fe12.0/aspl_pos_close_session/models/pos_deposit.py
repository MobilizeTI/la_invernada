from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class PosDeposit(models.Model):
    _name = 'pos.deposit'
    _description = 'Depositos desde el POS'

    name = fields.Char(string='Secuencial', size=255, 
        default = '/', readonly=True)
    user_deposit_id = fields.Many2one('res.users', 'Depositado por', readonly=True)
    user_confirm_id = fields.Many2one('res.users', 'Aprobado por', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', 
        readonly=True, states={'draft':[('readonly',False)]},
        default=lambda self: self.env.user.company_id)
    partner_company_id = fields.Many2one('res.partner', 'Empresa de compañia', related="company_id.partner_id")
    currency_id = fields.Many2one('res.currency', string='Currency', 
        default=lambda self: self.env.user.company_id.currency_id)
    session_id = fields.Many2one('pos.session', 'Sesion', 
        readonly=True)
    pos_config_id = fields.Many2one('pos.config', 'TPV',
        readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Tienda',
        readonly=True)
    cash_register_id = fields.Many2one('account.bank.statement', string="Registro de Caja",
        readonly=True)
    journal_id = fields.Many2one('account.journal', 'Diario',
        related='cash_register_id.journal_id', store=True)
    journal_dest_id = fields.Many2one('account.journal', 'Cuenta Bancaria', required=True,
        readonly=True, states={'draft':[('readonly',False)], 'sent':[('readonly',False)]})
    payment_ids = fields.One2many('account.payment', 'pos_deposit_id', 
        'Comprobante de Pago', auto_join=True, readonly=True)
    deposit_date = fields.Date('Fecha de Deposito', 
        readonly=True)
    papeleta_number = fields.Char('Numero de papeleta', 
        size=256, readonly=True, states={'sent':[('readonly',False)]})
    amount_cash = fields.Monetary(u'Efectivo a Depositar',
        readonly=True)
    state = fields.Selection(
        [('draft','Borrador'),
        ('sent','Enviado a depositar'),
        ('done','Depositado'),
        ('cancel','Cancelado'),
        ], string='Estado', index=True, readonly=True, default='draft')
    
    @api.multi
    def unlink(self):
        for deposit in self:
            if deposit.state not in ('draft', 'cancel'):
                raise UserError("No puede cancelar este depósito, intente cancelarlo primero")
        res = super(PosDeposit, self).unlink()
        return res
    
    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code(self._name)
        new_rec = super(PosDeposit, self).create(vals)
        return new_rec
    
    @api.multi
    def get_payment_values(self, deposit_type=None):
        payment_vals = {
            'payment_date': self.deposit_date,
            'communication': '%s %s' % (self.name, (": " + self.papeleta_number if self.papeleta_number else '')),
            'payment_type': 'outbound',
            'partner_type': 'customer',
            'partner_id': self.env.user.company_id.partner_id.id,
            'journal_id': self.journal_id.id,
            'amount': self.amount_cash,
            'currency_id': self.env.user.company_id.currency_id.id,
            'pos_deposit_id': self.id,
        }
        if deposit_type == 'done':
            payment_vals['journal_id'] = self.journal_dest_id.id
            payment_vals['payment_type'] = 'inbound'
        elif self.cash_register_id:
            payment_vals['apply_cash_register'] = True
            payment_vals['cash_register_id'] = self.cash_register_id.id
        return payment_vals
    
    @api.multi
    def action_sent(self):
        payment_model =  self.env['account.payment']
        for deposit in self:
            new_payment = payment_model.new(deposit.get_payment_values())
            new_payment._onchange_journal()
            payment_vals = payment_model._convert_to_write({name: new_payment[name] for name in new_payment._cache})
            new_payment = payment_model.create(payment_vals)
            new_payment.post()
        self.write({'state': 'sent', 'user_deposit_id': self.env.uid})
        return True
        
    @api.multi
    def action_done(self):
        payment_model =  self.env['account.payment']
        for deposit in self:
            new_payment = payment_model.new(deposit.get_payment_values('done'))
            new_payment._onchange_journal()
            payment_vals = payment_model._convert_to_write({name: new_payment[name] for name in new_payment._cache})
            new_payment = payment_model.create(payment_vals)
            new_payment.post()
        self.write({'state': 'done', 'user_confirm_id': self.env.uid})
        
    @api.multi
    def action_cancel(self):
        #cancelar los pagos y borrar el numero de asiento contable, para que se puedan eliminar sin problemas
        for deposit in self:
            if deposit.payment_ids:
                deposit.payment_ids.cancel()
                deposit.payment_ids.action_draft()
                deposit.payment_ids.unlink()
        self.write({'state': 'cancel'})
        return True
    
    @api.model
    def action_get_journal_for_deposit(self):
        Journals = self.env['account.journal'].search([
            ('type','=','bank'), 
            ('bank_account_id','!=',False), 
            ('bank_account_id.partner_id','=', self.env.user.company_id.partner_id.id),
        ])
        return Journals.read(fields=['name'])

    @api.multi
    def action_view_payments(self):
        ctx = self.env.context.copy()
        ctx['search_default_outbound_filter'] = False
        ctx['search_default_inbound_filter'] = False
        return self.env['odoo.utils'].with_context(ctx).show_action('account.action_account_payments', [('id', 'in', self.payment_ids.ids)]) 
