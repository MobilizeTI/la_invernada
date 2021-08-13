from collections import OrderedDict

from odoo import models, api, fields
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class PosInvoiceReport(models.AbstractModel):
    _name = 'report.aspl_pos_close_session.pos_session_resume'
    _description = 'Resumen de cajas'
    
    def _get_default_data(self, warehouse, date_from, date_to):
        return {
            'tickets_num': 0,
            'ticket_first_id': self.env['pos.order'].browse(),
            'ticket_last_id': self.env['pos.order'].browse(),
            'statement_data': OrderedDict(),
            'statements_total': 0,
            'statements_bank_total': 0,
            'cash_register_balance_start': 0,
            'cash_register_total_entry_encoding_custom': 0,
            'cash_register_total_entry_encoding_put_in': 0,
            'cash_register_total_entry_encoding_take_out': 0,
            'cash_register_total_entry_encoding_adjustment': 0,
            'cash_register_total_entry_encoding_deposit': 0,
            'cash_register_balance_end': 0,
            'cash_register_balance_end_real': 0,
            'cash_register_difference': 0,
            'statements_cn_total': 0.0,
            'statement_cn_data': OrderedDict(),
        }
        
    def _find_pos_sessions(self, warehouse, date_from, date_to):
        pos_config_recs = self.env['pos.config'].search([('warehouse_id', '=', warehouse.id)])
        pos_session = self.env['pos.session'].browse()
        if pos_config_recs:
            pos_session = self.env['pos.session'].search([
                ('config_id','in', pos_config_recs.ids),
                ('start_at','>=', date_from),
                ('stop_at','<=', date_to),
            ], order="start_at")
        return pos_session
    
    def _prepare_statement_vals(self, warehouse, date_from, date_to, pos_session, statement, session_data):
        session_data['statement_data'].setdefault(statement.journal_id, {'amount': 0.0, 'payment_count': 0})
        session_data['statement_data'][statement.journal_id]['amount'] += statement.total_entry_encoding_custom
        session_data['statement_data'][statement.journal_id]['payment_count'] += statement.payment_count
        if abs(statement.total_entry_encoding_cn) > 0:
            session_data['statement_cn_data'].setdefault(statement.journal_id, {'amount': 0.0, 'payment_count': 0})
            session_data['statement_cn_data'][statement.journal_id]['amount'] += statement.total_entry_encoding_cn
            session_data['statement_cn_data'][statement.journal_id]['payment_count'] += statement.payment_count
        return session_data
        
    def _prepare_session_vals(self, warehouse, date_from, date_to, pos_session, session_data):
        session_data['tickets_num'] += pos_session.tickets_num
        session_data['statements_total'] += pos_session.statements_total
        session_data['statements_bank_total'] += pos_session.statements_bank_total
        session_data['cash_register_balance_start'] += pos_session.cash_register_balance_start
        session_data['cash_register_total_entry_encoding_custom'] += pos_session.cash_register_total_entry_encoding_custom
        session_data['cash_register_total_entry_encoding_put_in'] += pos_session.cash_register_total_entry_encoding_put_in
        session_data['cash_register_total_entry_encoding_take_out'] += pos_session.cash_register_total_entry_encoding_take_out
        session_data['cash_register_total_entry_encoding_deposit'] += pos_session.cash_register_total_entry_encoding_deposit
        session_data['cash_register_total_entry_encoding_adjustment'] += pos_session.cash_register_total_entry_encoding_adjustment
        session_data['cash_register_balance_end'] += pos_session.cash_register_balance_end
        session_data['cash_register_balance_end_real'] += pos_session.cash_register_balance_end_real
        session_data['cash_register_difference'] += pos_session.cash_register_difference
        session_data['statements_cn_total'] += pos_session.statements_cn_total
        for statement in pos_session.statement_ids:
            self._prepare_statement_vals(warehouse, date_from, date_to, pos_session, statement, session_data)
        return session_data
    
    def _get_warehouse_data(self, warehouse, date_from, date_to):
        session_data = self._get_default_data(warehouse, date_from, date_to)
        pos_sessions = self._find_pos_sessions(warehouse, date_from, date_to)
        if pos_sessions:
            session_data['ticket_first_id'] = pos_sessions[0].ticket_first_id
            session_data['ticket_last_id'] = pos_sessions[-1].ticket_last_id
        for pos_session in pos_sessions:
            self._prepare_session_vals(warehouse, date_from, date_to, pos_session, session_data)
        return session_data

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data:
            data = {}
        form_data = data.get('form') or {}
        WarehouseModel = self.env['stock.warehouse']
        date_from = form_data.get('date_from', False)
        date_to = form_data.get('date_to', False)
        docids = form_data.get('warehouse_ids') or []
        docargs = {
            'doc_ids': docids,
            'doc_model': WarehouseModel._name,
            'data': data,
            'docs': WarehouseModel.browse(docids),
            'date_from': date_from,
            'date_to': date_to,
            'get_warehouse_data': self._get_warehouse_data,
        }
        return docargs
