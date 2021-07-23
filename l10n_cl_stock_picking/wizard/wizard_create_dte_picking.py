from datetime import datetime, timedelta

from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class WizardCreateDtePicking(models.TransientModel):
    _name = 'wizard.create.dte.picking'
    _description = 'Asistente para crear Guia de despacho en picking'
    
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
    picking_id = fields.Many2one('stock.picking', string="Picking actual")
    carrier_id = fields.Many2one('delivery.carrier', string="Transportista")
    patente = fields.Char(string="Patente")
    
    @api.model
    def default_get(self, fields_list):
        values = super(WizardCreateDtePicking, self).default_get(fields_list)
        PickingModel = self.env['stock.picking']
        if self.env.context.get('active_ids') and self.env.context.get('active_model') == PickingModel._name:
            picking = PickingModel.browse(self.env.context.get('active_ids')[0])
            values.update({
                'transport_type': picking.transport_type,
                'move_reason': picking.move_reason,
                'patente': picking.patente,
                'vehicle': picking.vehicle.id,
                'chofer': picking.chofer.id,
                'partner_id': picking.partner_id.id,
                'contact_id': picking.contact_id.id,
                'carrier_id': picking.carrier_id.id,
                'picking_id': picking.id,
            })
        return values

    def action_process(self):
        referencias = []
        for invoice in self.picking_id.invoice_ids:
            referencias = [(0,0, {
                'origen': int(invoice.sii_document_number),
                'sii_referencia_TpoDocRef': invoice.document_class_id.id,
                'date': invoice.date_invoice,
            })]
        picking_vals = {
            'use_documents': True,
            'transport_type': self.transport_type,
            'move_reason': self.move_reason,
            'vehicle': self.vehicle.id,
            'chofer': self.chofer.id,
            'partner_id': self.partner_id.id,
            'contact_id': self.contact_id.id,
            'carrier_id': self.carrier_id.id,
            'patente': self.patente,
            'responsable_envio': self.env.uid,
            'sii_result': 'NoEnviado',
            'reference': referencias,
        }
        # escribir nuevos datos y asegurarse de asignar folio
        self.picking_id.write(picking_vals)
        if not self.picking_id.sii_document_number and self.picking_id.location_id.sequence_id.is_dte:
            sii_document_number = self.picking_id.location_id.sequence_id.next_by_id()
            document_number = (self.picking_id.document_class_id.doc_code_prefix or '') + sii_document_number
            self.picking_id.write({
                'sii_document_number': sii_document_number,
                'name': document_number,
            })
        # timbrar y enviar a la cola de envio
        self.picking_id._timbrar()
        tiempo_pasivo = (datetime.now() + timedelta(hours=int(self.env['ir.config_parameter'].sudo().get_param('account.auto_send_dte', default=12))))
        self.env['sii.cola_envio'].create({
            'doc_ids': [self.picking_id.id],
            'model': 'stock.picking',
            'user_id': self.env.uid,
            'tipo_trabajo': 'pasivo',
            'date_time': tiempo_pasivo,
        })
        return {'type': 'ir.actions.act_window_close'}
    