from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class PosConfig(models.Model):
    _inherit = 'pos.config'
    
    @api.multi
    def action_create_sequence_by_pos(self):
        JournalSequences = self.env['account.journal.pos.sequence']
        Journals = self.env['account.journal']
        Sequences = self.env['ir.sequence']
        for config in self:
            for payment in config.journal_ids:
                if not payment.pos_sequence_ids.filtered(lambda x: x.pos_config_id == config):
                    sequence = Sequences.create({
                        'name': '%s %s' % (config.name, payment.code),
                        'implementation': 'no_gap',
                        'prefix': Journals._get_sequence_prefix(payment.code),
                        'padding': 4,
                        'number_increment': 1,
                        'use_date_range': True,
                    })
                    JournalSequences.create({
                        'journal_id': payment.id,
                        'sequence_id': sequence.id,
                        'pos_config_id': config.id,
                    })
        return True