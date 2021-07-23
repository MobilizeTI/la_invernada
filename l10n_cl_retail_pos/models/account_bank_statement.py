from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools import formatLang


class AccountBankStatementLine(models.Model):    
    _inherit = 'account.bank.statement.line'
    
    @api.multi
    def _is_credit_note(self):
        is_credit_note = False
        if self.pos_statement_id and self.pos_statement_id.document_class_id and self.pos_statement_id.document_class_id.sii_code == 61:
            is_credit_note = True
        if self.force_is_credit_note:
            is_credit_note = True
        return is_credit_note
