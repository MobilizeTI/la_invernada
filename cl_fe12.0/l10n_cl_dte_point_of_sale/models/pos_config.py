from odoo import fields, models, api, _


class PosConfig(models.Model):
    _inherit = "pos.config"

    
    #campos para valores por defecto al crear clientes en el pos
    sii_responsability_id = fields.Many2one('sii.responsability', 'Responsabilidad')
    sii_document_type_id = fields.Many2one('sii.document_type', 'Tipo de Documento')
    # nuevos campos
    address_id = fields.Many2one('res.partner', 'Direccion de Sucursal')
    address_street = fields.Char('Direccion', related="address_id.street", store=True)
    address_city = fields.Char('Ciudad', related="address_id.city", store=True)
    caja_number = fields.Char('Numero de Caja')
    sequence_available_ids = fields.Many2many('ir.sequence', 
        'pos_config_sii_sequence_rel', 'pos_config_id', 'sequence_id', 
        'Documentos Disponibles en POS',)
    default_sequence_id = fields.Many2one('ir.sequence', 'Documento por Defecto')
    cn_sequence_id = fields.Many2one('ir.sequence', 'Secuencia para NC')
    enable_change_document_type = fields.Boolean('Permitir Cambiar Tipo de Documento?')
    create_picking = fields.Boolean('Crear Picking de Pedidos automaticamente?', default=True)
    create_picking_account_move = fields.Boolean('Crear Asiento contable de Pedidos automaticamente?', default=True)
    timbrar_online = fields.Boolean('Timbrar Pedidos automaticamente?', default=True)
    ticket = fields.Boolean(
            string="¿Facturas en Formato Ticket?",
            default=False,
    )
    restore_mode = fields.Boolean(
        string="Restore Mode",
        default=False,
    )

    @api.onchange('sequence_available_ids')
    def _onchange_sequence_available(self):
        if self.default_sequence_id not in self.sequence_available_ids:
            self.default_sequence_id = False
            
    @api.onchange('journal_id',)
    def onchange_journal(self):
        self.invoice_journal_id = self.journal_id.id
