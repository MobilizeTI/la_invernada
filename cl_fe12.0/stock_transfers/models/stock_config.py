from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class StockConfig(models.TransientModel):
    _inherit = 'res.config.settings'
    
    internal_transfer_steps = fields.Selection([
        ('2_step','2 pasos(Despacho, Recepcion)'),
        ('3_step','3 pasos(Solicitud, Despacho, Recepcion)'),
        ], string='Realizar transferencia en', default='2_step',
        related='company_id.internal_transfer_steps', readonly=False,)
    internal_transfer_partial_reception = fields.Selection([
        ('create_backorder','Recepcion parcial(Con backorder)'),
        ('return_remaining','Devolver restantes'),
        ], string='Politica de recepcion incompleta', default='create_backorder',
        related='company_id.internal_transfer_partial_reception', readonly=False,)
    transfer_auto_validate_picking = fields.Boolean(u'Validar picking automaticamente?',
        related='company_id.transfer_auto_validate_picking', readonly=False,)
    transfer_create_account_move = fields.Boolean(u'Crear asiento contable de transferencias?',
        related='company_id.transfer_create_account_move', readonly=False,)
