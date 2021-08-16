# -*- coding: utf-8 -*-

from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _

class PosSessionDocumentAvailable(models.Model):

    _name = 'pos.session.document.available'
    _description = 'Informacion de documentos disponibles a emitir en pos'
    
    caf_files = fields.Char('CAF')
    next_document_number = fields.Integer('Siguiente Numero', readonly=True)
    last_document_number = fields.Integer('Ultimo Numero autorizado', readonly=True)
    document_class_id = fields.Many2one(
        'sii.document_class',
        string='Document Type',
        copy=False,
        readonly=True,
        ondelete="restrict",
        index=True
    )
    sequence_id = fields.Many2one('ir.sequence', 'Secuencia', 
        readonly=True, ondelete="restrict", index=True)
    pos_session_id = fields.Many2one('pos.session', 'Sesion del POS', ondelete="cascade")
