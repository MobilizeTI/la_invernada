from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class WizardCreatePickingFromInvoice(models.TransientModel):
    _name = 'wizard.create.picking.from.invoice'
    _description = 'Asistente para crear picking desde factura'
    
    use_documents = fields.Boolean(string='Generar Guia de despacho electronica?',
        default=True)
    transport_type = fields.Selection([
        ('2', 'Despacho por cuenta de empresa'),
        ('1', 'Despacho por cuenta del cliente'),
        ('3', 'Despacho Externo'),
        ('0', 'Sin Definir')
        ], string="Tipo de Despacho", default="0",
    )
    move_reason = fields.Selection([
        ('1', 'Operación constituye venta'),
        ('2', 'Ventas por efectuar'),
        ('3', 'Consignaciones'),
        ('4', 'Entrega Gratuita'),
        ('5', 'Traslados Internos'),
        ('6', 'Otros traslados no venta'),
        ('7', 'Guía de Devolución'),
        ('8', 'Traslado para exportación'),
        ('9', 'Ventas para exportación')
        ], string='Razón del traslado', default="5",
    )
    vehicle = fields.Many2one('fleet.vehicle', string="Vehículo")
    chofer = fields.Many2one('res.partner', string="Chofer")
    partner_id = fields.Many2one('res.partner', string="Cliente destino")
    contact_id = fields.Many2one('res.partner', string="Contacto")
    patente = fields.Char(string="Patente")
    # campo para tener referencia a la factura actual
    invoice_id = fields.Many2one('account.invoice', 'Factura')

    @api.onchange('use_documents')
    def _onchange_use_documents(self):
        if self.use_documents and self.invoice_id:
            self.partner_id = self.invoice_id.partner_id.id
            
    def action_process(self):
        picking_vals = {
            'use_documents': self.use_documents,
            'transport_type': self.transport_type,
            'move_reason': self.move_reason,
            'vehicle': self.vehicle.id,
            'chofer': self.chofer.id,
            'partner_id': self.partner_id.id,
            'contact_id': self.contact_id.id,
            'patente': self.patente,
        }
        ctx = self.env.context.copy()
        ctx['picking_info_aditional'] = picking_vals
        # pasar esto par que no vuelva a levantar el asistente y cree el picking
        ctx['create_picking_from_wizard'] = True
        self.invoice_id.with_context(ctx).action_create_picking()
        return {'type': 'ir.actions.act_window_close'}
