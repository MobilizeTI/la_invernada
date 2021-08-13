from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class AccountJournalDocumentConfig(models.TransientModel):
    _inherit = 'account.journal.document_config'
    
    create_documents_for_pos = fields.Boolean(u'Crear Documentos para POS?')
    pos_document_ids = fields.Many2many('sii.document_class', 'account_journal_document_config_sii_document_class_rel', 
        'wizard_journal_id', 'document_class_id', u'Tipos de documentos')
    pos_config_ids = fields.Many2many('pos.config', 'account_journal_document_config_pos_config_rel', 
        'wizard_journal_id', 'pos_config_id', u'TPV')
    
    def create_journals(self, journal_ids):
        res = super(AccountJournalDocumentConfig, self).create_journals(journal_ids)
        if self.create_documents_for_pos:
            IrSequence = self.env['ir.sequence']
            journal_document_obj = self.env['account.journal.sii_document_class']
            sequence = 100
            for journal in self.env['account.journal'].browse(journal_ids):
                for pos in self.pos_config_ids:
                    sequence_ids = pos.sequence_available_ids.ids
                    for sii_document in self.pos_document_ids:
                        # al nombre de la secuencia agregarle el nombre del TPV para poder diferenciar
                        sequence_name = "%s - %s - %s" % (pos.name, sii_document.name, journal.name)
                        if self._find_current_document(journal, sii_document, sequence_name):
                            continue
                        sequence_vals = self.create_sequence(sequence_name, journal, sii_document)
                        new_sequence =  IrSequence.create(sequence_vals)
                        sequence_ids.append(new_sequence.id)
                        vals = {
                            'sii_document_class_id': sii_document.id,
                            'sequence_id': new_sequence.id,
                            'journal_id': journal.id,
                            'sequence': sequence,
                        }
                        journal_document_obj.create(vals)
                        sequence += 10
                    pos.write({
                        'sequence_available_ids': [(6, 0, sequence_ids)],
                        'enable_change_document_type': len(sequence_ids) > 1,
                    })
        return res
