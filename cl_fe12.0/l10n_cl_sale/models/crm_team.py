from odoo import models, fields, api


class CrmTeam(models.Model):    
    _inherit = 'crm.team'
    
    journal_document_class_id = fields.Many2one(
        'account.journal.sii_document_class',
        'Tipo de Documento(Factura)',)
    journal_document_class_boleta_id = fields.Many2one(
        'account.journal.sii_document_class',
        'Tipo de Documento(Boleta)',)
    payment_journal_id = fields.Many2one(
        'account.journal',
        'Diario de Pagos por defecto',)
