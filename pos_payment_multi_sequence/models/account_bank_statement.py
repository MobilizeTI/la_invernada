from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'
    
    def _prepare_reconciliation_move(self, move_ref):
        if not self.move_name and self.journal_id.pos_sequence_ids and self.statement_id.pos_session_id:
            sequence_pos = self.journal_id.pos_sequence_ids.filtered(lambda x: x.pos_config_id == self.statement_id.pos_session_id.config_id)
            if sequence_pos:
                self.move_name = sequence_pos.sequence_id.with_context(ir_sequence_date=self.date).next_by_id()
        return super(AccountBankStatementLine, self)._prepare_reconciliation_move(move_ref)