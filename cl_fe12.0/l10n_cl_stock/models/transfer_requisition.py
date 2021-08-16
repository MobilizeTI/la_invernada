from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _

STATES = {'draft':[('readonly',False)]}


class TransferRequisition(models.Model):
    _inherit = 'transfer.requisition'
    
    use_documents = fields.Boolean(string='Generar Guia de despacho electronica?',
        default=True, readonly=True, states=STATES)
    transport_type = fields.Selection([
        ('2', 'Despacho por cuenta de empresa'),
        ('1', 'Despacho por cuenta del cliente'),
        ('3', 'Despacho Externo'),
        ('0', 'Sin Definir')
        ], string="Tipo de Despacho", default="0", readonly=True, states=STATES,
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
        readonly=True, states=STATES,
    )
    vehicle = fields.Many2one('fleet.vehicle', string="Vehículo", 
        readonly=True, states=STATES,
    )
    chofer = fields.Many2one('res.partner', string="Chofer",
        readonly=True, states=STATES,
    )
    partner_id = fields.Many2one('res.partner', string="Cliente destino",
        readonly=True, states=STATES,
    )
    contact_id = fields.Many2one('res.partner', string="Contacto",
        readonly=True, states=STATES,
    )
    patente = fields.Char(string="Patente",
        readonly=True, states=STATES,
    )
    
    @api.model
    def _get_extra_domain(self):
        user_model = self.env['res.users']
        domain = []
        location_ids = []
        if not user_model.has_group('stock.group_stock_manager') \
                and not user_model.has_group('l10n_cl_stock.group_validate_guias') \
                and not self.env.context.get('show_all_location',False):
            location_ids = user_model.get_all_location().ids
            if location_ids:
                domain.append('|')
                domain.append(('location_id','in', location_ids))
                domain.append(('location_dest_id','in', location_ids))
        return domain
    
    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        args.extend(self._get_extra_domain())
        res = super(TransferRequisition, self)._search(args=args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
        return res
    
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        domain.extend(self._get_extra_domain())
        res = super(TransferRequisition, self).read_group(domain=domain, fields=fields, groupby=groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return res
    
    @api.multi
    def _prepare_stock_picking(self, picking_type, location, location_dest, origin, picking_date, internal_type):
        picking_vals = super(TransferRequisition, self)._prepare_stock_picking(picking_type, location, location_dest, origin, picking_date, internal_type)
        picking_vals.update({
            'transport_type': self.transport_type,
            'move_reason': self.move_reason,
            'vehicle': self.vehicle.id,
            'chofer': self.chofer.id,
            'partner_id': self.partner_id.id,
            'contact_id': self.contact_id.id,
            'patente': self.patente,
            'use_documents': False,
        })
        if internal_type == 'dispatch':
            picking_vals['use_documents'] = self.use_documents
        return  picking_vals
    
    @api.model
    def _get_vals_move(self, line, picking, location, location_dest):
        vals = super(TransferRequisition, self)._get_vals_move(line, picking, location, location_dest)
        vals.update({
            'name': line.product_id.display_name,
            'precio_unitario': line.product_id.lst_price,
            'move_line_tax_ids': [(6, 0, line.product_id.taxes_id.ids)],
        })
        return vals
    
    @api.multi
    def action_request(self):
        return super(TransferRequisition, self.with_context(force_validation_stock=True)).action_request()
    
    @api.multi
    def _action_approved(self):
        return super(TransferRequisition, self.with_context(force_validation_stock=True))._action_approved()
    
    @api.multi
    def _action_receive(self):
        return super(TransferRequisition, self.with_context(force_validation_stock=True))._action_receive()

class TransferRequisitionLine(models.Model):
    _inherit = 'transfer.requisition.line'
    
    @api.onchange('product_qty', 'qty_process', 'uom_id')
    def onchange_product_qty(self):
        return super(TransferRequisitionLine, self.with_context(force_validation_stock=True)).onchange_product_qty()
