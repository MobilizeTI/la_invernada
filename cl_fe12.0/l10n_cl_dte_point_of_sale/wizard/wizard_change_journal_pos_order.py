from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class WizardChangeJournalPosOrder(models.TransientModel):
    _name = 'wizard.change.journal.pos.order'
    _description = 'Asistente para cambio de pagos en PDV'
    
    order_id = fields.Many2one('pos.order', 'Pedido de Venta')
    session_id = fields.Many2one('pos.session', 'Sesion', required=False, related='order_id.session_id', store=False)
    payment_id = fields.Many2one('account.bank.statement.line', 'Pago a modificar')
    statement_id = fields.Many2one('account.bank.statement', 'Nuevo Pago')
    journal_currency_id = fields.Many2one('res.currency', related='statement_id.currency_id', readonly=True)
    total = fields.Monetary('Total', digits=dp.get_precision('Account'), 
        related="payment_id.amount", currency_field='journal_currency_id', store=False)
    
    @api.model
    def default_get(self, fields_list):
        values = super(WizardChangeJournalPosOrder, self).default_get(fields_list)
        order_model = self.env['pos.order']
        if self.env.context.get('active_model', '') == order_model._name and self.env.context.get('active_id', False):
            order = order_model.browse(self.env.context.get('active_id'))
            if order.session_id.state not in ('opened',):
                raise UserError("No puede hacer esta operacion porque la sesion %s no esta abierta, contacte con su administrador" % (order.session_id.display_name))
            values['order_id'] = order.id
        return values
    
    @api.multi
    def action_process(self):
        self.payment_id.write({
            'statement_id': self.statement_id.id,
            'amount': self.payment_id.amount, 
        })
        return {'type': 'ir.actions.act_window_close'}
