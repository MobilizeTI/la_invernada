# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

import logging
from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare

_logger = logging.getLogger(__name__)


class pos_session(models.Model):
    _inherit = 'pos.session'

    @api.one
    @api.depends('statement_ids','statement_ids.total_entry_encoding', 'statement_ids.total_entry_encoding_custom', 'statement_ids.total_entry_encoding_cn')
    def _compute_amount_custom(self):
        statements_total, statements_bank_total = 0.0, 0.0
        total_cn = 0.0
        for st in self.statement_ids:
            # si es el diario de efectivo, mostrar solo las ventas, no saldo inicial ni ingresos/egreos
            # pero otros diarios si mostrar ingresos y egresos, para que no haya descuadre
            if st == self.cash_register_id:
                statements_total += st.total_entry_encoding_custom
            else:
                statements_total += st.total_entry_encoding
            if st.journal_id.type == 'bank':
                statements_bank_total += st.total_entry_encoding
            total_cn += st.total_entry_encoding_cn
        self.statements_total = statements_total
        self.statements_bank_total = statements_bank_total
        self.statements_cn_total = total_cn
        
    @api.one
    @api.depends('order_ids',)
    def _compute_tickets(self):
        orders = self.order_ids.sorted('id')
        self.tickets_num = len(orders)
        ticket_null = self.env['pos.order'].browse()
        self.ticket_first_id = orders[0] if orders else ticket_null
        self.ticket_last_id = orders[-1] if orders else ticket_null
                
    cash_register_total_entry_encoding_custom = fields.Monetary('Total Sales', 
        related='cash_register_id.total_entry_encoding_custom', readonly=True)
    cash_register_total_entry_encoding_put_in = fields.Monetary('Cash put in', 
        related='cash_register_id.total_entry_encoding_put_in', readonly=True)
    cash_register_total_entry_encoding_take_out = fields.Monetary('Cash take out', 
        related='cash_register_id.total_entry_encoding_take_out', readonly=True)
    cash_register_total_entry_encoding_deposit = fields.Monetary('Deposit', 
        related='cash_register_id.total_entry_encoding_deposit', readonly=True)
    cash_register_total_entry_encoding_adjustment = fields.Monetary('Total Ajustes de cierre', 
        related='cash_register_id.total_entry_encoding_adjustment', readonly=True)
    statements_total = fields.Monetary('Total Payments Received', 
        compute='_compute_amount_custom', readonly=True, store=True)
    statements_bank_total = fields.Monetary('Otros Medios', 
        compute='_compute_amount_custom', readonly=True, store=True)
    statements_cn_total = fields.Monetary('Total Notas de Credito', 
        compute='_compute_amount_custom', store=True)
    tickets_num = fields.Integer('Number of Tickets', compute='_compute_tickets', store=True)
    ticket_first_id = fields.Many2one('pos.order', 'First Ticket', compute='_compute_tickets', store=True)
    ticket_last_id = fields.Many2one('pos.order', 'Last Ticket', compute='_compute_tickets', store=True)
    opening_balance = fields.Boolean(string="Opening Balance")
    cash_control_start_ids = fields.Many2many('account.cashbox.line', compute='_compute_cash_control_data')
    cash_control_end_ids = fields.Many2many('account.cashbox.line', compute='_compute_cash_control_data')
    pos_deposit_ids = fields.One2many('pos.deposit', 'session_id', 'Depositos', readonly=True)
    payment_resume_ids = fields.One2many('pos.session.payment.resume', 'session_id', u'Resument de pagos', readonly=True)
    
    @api.depends()
    def _compute_cash_control_data(self):
        for session in self:
            if session.cash_register_id:
                if session.cash_register_id.cashbox_start_id:
                    session.cash_control_start_ids = session.cash_register_id.cashbox_start_id.cashbox_lines_ids.filtered(lambda x: x.number).ids
                if session.cash_register_id.cashbox_end_id:
                    session.cash_control_end_ids = session.cash_register_id.cashbox_end_id.cashbox_lines_ids.filtered(lambda x: x.number).ids

    @api.model
    def send_email_z_report(self, pos_session_id):
        try:
            pos_session = self.env['pos.session'].browse(pos_session_id)
            email_list = ",".join(filter(None, pos_session.config_id.users_ids.mapped('email')))
            mail_template = pos_session.config_id.email_template_id.with_context(email_to=email_list)
            temp_name = 'aspl_pos_close_session.pos_z_report_template'
            report_id = self.env['ir.actions.report'].search([('report_name','=',temp_name)])
            if mail_template and report_id:
                mail_template.write({
                    'report_name':'Z Report',
                    'report_template':report_id.id,
                })
                mail_template.send_mail(pos_session.id, force_send=True, raise_exception=True)
            else:
                _logger.error('Mail Template and Report not defined!')
        except Exception as e:
            _logger.error('Unable to send email for z report of session %s', e)
        return pos_session
    
    @api.multi
    def action_pos_session_open(self):
        res = super(pos_session, self).action_pos_session_open()
        self.action_create_payment_resume()
        return res
    
    @api.multi
    def action_create_payment_resume(self):
        PaymentResumeModel = self.env['pos.session.payment.resume']
        PaymentResume = PaymentResumeModel.browse()
        for session in self:
            for credit_card in session.statement_ids.mapped('journal_id').mapped('credit_card_provider_id'):
                PaymentResume |= PaymentResumeModel.create({
                    'credit_card_provider_id': credit_card.id,
                    'session_id': session.id,
                })
        return PaymentResume

    @api.multi
    def custom_close_pos_session(self):
        self._check_pos_session_balance()
        self.write({'state': 'closing_control', 'stop_at': fields.Datetime.now()})
        for session in self:
            if session.config_id.cash_control:
                self._check_pos_session_balance()
            return self.action_pos_session_close()

    @api.multi
    def close_open_balance(self):
        self.write({'opening_balance': False})
        return True

    @api.multi
    def set_close_balance(self, balance_end, cash_values):
        if self.cash_register_id:
            CashModel = self.env['account.bank.statement.cashbox']
            self.cash_register_id.write({'balance_end_real': balance_end})
            if cash_values:
                cashbox_lines = [(0, 0, val) for val in cash_values]
                if self.cash_register_id.cashbox_end_id:
                    # eliminar las lineas existentes para crearlas nuevamente
                    self.cash_register_id.cashbox_end_id.cashbox_lines_ids.sudo().unlink()
                    self.cash_register_id.cashbox_end_id.write({'cashbox_lines_ids': cashbox_lines})
                else:
                    self.cash_register_id.cashbox_end_id = CashModel.create({'cashbox_lines_ids': cashbox_lines})
        return True

    @api.multi
    def set_open_balance(self, balance_start, cash_values):
        if self.cash_register_id:
            CashModel = self.env['account.bank.statement.cashbox']
            self._check_balance_start(self.cash_register_id, balance_start)
            self.cash_register_id.write({'balance_start': balance_start})
            if cash_values:
                cashbox_lines = [(0, 0, val) for val in cash_values]
                if self.cash_register_id.cashbox_start_id:
                    # eliminar las lineas existentes para crearlas nuevamente
                    self.cash_register_id.cashbox_start_id.cashbox_lines_ids.sudo().unlink()
                    self.cash_register_id.cashbox_start_id.write({'cashbox_lines_ids': cashbox_lines})
                else:
                    self.cash_register_id.cashbox_start_id = CashModel.create({'cashbox_lines_ids': cashbox_lines})
        self.write({'opening_balance':False})
        return True
    
    @api.multi
    def _check_balance_start(self, cash_statement, balance_start):
        if cash_statement.pos_session_id and cash_statement.pos_session_id.config_id.no_change_cash_open:
            if float_compare(balance_start, cash_statement.balance_start, precision_digits=cash_statement.currency_id.decimal_places) != 0:
                raise ValidationError("El saldo de apertura ingresado es diferente al saldo de cierre de la session anterior, " \
                                      "no puede cambiar el saldo de apertura. " \
                                      "Solo puede contabilizar segun la denominacion de monedas, pero el total debe ser igual al saldo anterior")


class AccountBankStmtCashWizard(models.Model):
    _inherit = 'account.bank.statement.cashbox'
    
    payment_resumen_ids = fields.Many2many('pos.session.payment.resume', 
        'account_bank_statement_cashbox_payment_resume_rel', 'casbox_id', 'payment_resume_id', 'Resumen de Pagos', readonly=True)
    
    @api.model
    def default_get(self, fields):
        vals = super(AccountBankStmtCashWizard, self).default_get(fields)
        if self.env.context.get('balance', False) == 'end' and self.env.context.get('bank_statement_id'):
            bank_statement = self.env['account.bank.statement'].browse(self.env.context.get('bank_statement_id'))
            if bank_statement.pos_session_id:
                vals['payment_resumen_ids'] = bank_statement.pos_session_id.payment_resume_ids.ids
        return vals

    @api.multi
    def validate(self):
        if self.env.context.get('balance', False) == 'start':
            bnk_stmt_id = self.env.context.get('bank_statement_id', False) or self.env.context.get('active_id', False)
            bnk_stmt = self.env['account.bank.statement'].browse(bnk_stmt_id)
            if bnk_stmt.pos_session_id and bnk_stmt.pos_session_id.config_id.no_change_cash_open:
                total = 0.0
                for lines in self.cashbox_lines_ids:
                    total += lines.subtotal
                bnk_stmt.pos_session_id._check_balance_start(bnk_stmt, total)
        return super(AccountBankStmtCashWizard, self).validate()


class PosSessionPaymentResume(models.Model):
    _name = 'pos.session.payment.resume'
    _description = 'Resumen de pagos en session'
    
    @api.depends('session_id.statement_ids.line_ids.amount')
    def _compute_resume_values(self):
        for resumen in self:
            amount_total, payment_count = 0.0, 0.0
            for statement in resumen.session_id.statement_ids:
                if statement.journal_id.credit_card_provider_id == resumen.credit_card_provider_id:
                    # si es el diario de efectivo, mostrar solo las ventas, no saldo inicial ni ingresos/egreos
                    # pero otros diarios si mostrar ingresos y egresos, para que no haya descuadre
                    if statement == resumen.session_id.cash_register_id:
                        amount_total += statement.total_entry_encoding_custom
                    else:
                        amount_total += statement.total_entry_encoding
                    payment_count += statement.payment_count
            resumen.amount_total = amount_total
            resumen.payment_count = payment_count
    
    credit_card_provider_id = fields.Many2one('credit.card.provider', 
        'Grupo')
    session_id = fields.Many2one('pos.session', u'Session', ondelete="cascade")
    currency_id = fields.Many2one('res.currency', related='session_id.currency_id', string="Currency", readonly=False)
    amount_total = fields.Monetary('Total', 
        compute='_compute_resume_values', store=True)
    payment_count = fields.Integer('Cantidad Pagos', 
        compute='_compute_resume_values', store=True)
