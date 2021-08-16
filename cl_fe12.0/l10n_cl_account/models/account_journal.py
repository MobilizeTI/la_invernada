from odoo import models, api, fields


class AccountJournalSiiDocumentClass(models.Model):
    _inherit = 'account.journal.sii_document_class'
    
    @api.multi
    def name_get(self):
        res = []
        for document in self:
            name = "%s" % (document.sii_document_class_id.name)
            if document.sequence_id and self.env.context.get('show_full_name', False):
                name = "%s" % (document.sequence_id.name)
            res.append((document.id, name))
        return res
