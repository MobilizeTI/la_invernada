# -*- coding: utf-8 -*-
from odoo import models, api, fields

class PosOrder(models.Model):
    _inherit = "pos.order"
    
    payment_ref = fields.Char('Codigo de autorizacion(Pagos)', readonly=True, store=False, search='_search_payment_ref')
    
    @api.multi
    def _search_payment_ref(self, operator, value):
        recs = self.browse()
        if value:
            domain = [
                ('pos_statement_id', '!=', False),
                ('payment_ref', operator, value),
            ]
            recs = self.env['account.bank.statement.line'].search(domain).mapped('pos_statement_id')
        return [('id', 'in', recs.ids)]

    def _payment_fields(self, ui_paymentline):
        res = super(PosOrder, self)._payment_fields(ui_paymentline)
        res.update({
            'payment_ref': ui_paymentline.get('payment_ref'),
        })
        return res

    def add_payment(self, data):
        statement_id = super(PosOrder, self).add_payment(data)
        if data.get('payment_ref'):
            StatementLine = self.env['account.bank.statement.line']
            statement_lines = StatementLine.search([
                ('statement_id', '=', statement_id),
                ('pos_statement_id', '=', self.id),
                ('journal_id', '=', data['journal']),
                ('amount', '=', data['amount'])
            ])
            for line in statement_lines:
                if line.journal_id.pos_payment_ref :    
                    line.write({'payment_ref': data.get('payment_ref')})
        return statement_id
