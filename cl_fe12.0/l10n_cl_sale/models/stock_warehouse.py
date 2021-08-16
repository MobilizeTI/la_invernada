from odoo import models, fields, api

class StockWarehouse(models.Model):
    
    _inherit = 'stock.warehouse'
    
    journal_document_class_id = fields.Many2one(
        'account.journal.sii_document_class',
        'Tipo de Documento(Factura)',)
    journal_document_class_boleta_id = fields.Many2one(
        'account.journal.sii_document_class',
        'Tipo de Documento(Boleta)',)
