from odoo import fields, models, api
from odoo.tools.translate import _
from odoo.exceptions import UserError


class sii_document_class(models.Model):
    _inherit = 'sii.document_class'
    
    max_number_documents = fields.Integer(u'Numero maximo de lineas en documento')