from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    internal_transfer_steps = fields.Selection([
        ('2_step','2 pasos(Despacho, Recepcion)'),
        ('3_step','3 pasos(Solicitud, Despacho, Recepcion)'),
        ], string='Realizar transferencia en', default='2_step')
    internal_transfer_partial_reception = fields.Selection([
        ('create_backorder','Recepcion parcial(Con backorder)'),
        ('return_remaining','Devolver restantes'),
        ], string='Politica de recepcion incompleta', default='create_backorder')
    transfer_auto_validate_picking = fields.Boolean(u'Validar picking automaticamente?')
    transfer_create_account_move = fields.Boolean(u'Crear asiento contable de transferencias?')
    
    def create_sequence_for_transfers(self):
        Sequences = self.env['ir.sequence']
        for company in self:
            current_sequence = Sequences.search([
                ('code', '=', 'transfer.requisition'),
                '|',
                ('company_id', '=', company.id),
                ('company_id', '=', False),
            ], limit=1)
            if not current_sequence:
                Sequences.create({
                    'name': 'Solicitud de Transferencia',
                    'code': 'transfer.requisition',
                    'prefix': 'TRAN-',
                    'padding': 6,
                    'company_id': company.id,
                })

    @api.model
    def create(self, vals):
        company = super(ResCompany, self).create(vals)
        company.create_sequence_for_transfers()
        return company
