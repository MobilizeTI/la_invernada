from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class AccountJournal(models.Model):
    _inherit = 'account.journal'
    
    pos_sequence_ids = fields.One2many('account.journal.pos.sequence', 
        'journal_id', u'Secuencias por TPV')
    

class AccountJournalPosSequence(models.Model):
    _name = 'account.journal.pos.sequence'
    _description = 'Secuencias de pos por diario'
    
    journal_id = fields.Many2one('account.journal', u'Diario', ondelete="cascade")
    sequence_id = fields.Many2one('ir.sequence', u'Secuencia', ondelete="restrict")
    pos_config_id = fields.Many2one('pos.config', u'TPV', ondelete="cascade")
    
    _sql_constraints = [('journal_by_pos_uniq', 'unique (journal_id, pos_config_id)', 'Ya existe otro registro de secuencia para el mismo TPV en el mismo diario de pago'), ]
