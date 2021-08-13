from datetime import datetime

from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

class account_invoice(models.Model):

    _inherit = 'account.invoice'
    
    create_picking = fields.Boolean('Crear Picking?', copy=False)
    stock_move_date = fields.Datetime(u'Fecha de Inventario')
    picking_type_id = fields.Many2one('stock.picking.type', 'Tipo de Operacion')
    
    def _get_last_step_stock_moves(self):
        """ Overridden from stock_account.
        Returns the stock moves associated to this invoice."""
        rslt = super(account_invoice, self)._get_last_step_stock_moves()
        for invoice in self.filtered(lambda x: x.type == 'in_invoice'):
            rslt += invoice.mapped('invoice_line_ids.move_line_ids').filtered(lambda x: x.state == 'done' and x.location_id.usage == 'supplier')
        for invoice in self.filtered(lambda x: x.type == 'in_refund'):
            rslt += invoice.mapped('invoice_line_ids.move_line_ids').filtered(lambda x: x.state == 'done' and x.location_dest_id.usage == 'supplier')
        for invoice in self.filtered(lambda x: x.type == 'out_invoice'):
            rslt += invoice.mapped('invoice_line_ids.move_line_ids').filtered(lambda x: x.state == 'done' and x.location_dest_id.usage == 'customer')
        for invoice in self.filtered(lambda x: x.type == 'out_refund'):
            rslt += invoice.mapped('invoice_line_ids.move_line_ids').filtered(lambda x: x.state == 'done' and x.location_id.usage == 'customer')
        return rslt
    
    @api.multi
    def _get_date_from_picking(self):
        date_picking = self.env.context.get('stock_move_date') or self.stock_move_date
        if not date_picking and self.date_invoice:
            date_picking = "%s %s" % (self.date_invoice, datetime.now().strftime('%H:%M:%S'))
        if not date_picking:
            date_picking = fields.Datetime.now()
        return date_picking
    
    @api.multi
    def _get_stock_picking_type(self):
        return self.picking_type_id
        
    @api.multi
    def _get_locations_from_picking(self, picking_type):
        location_id, location_dest_id = False, False
        if self.type == 'in_invoice':
            location_id = self.partner_id.property_stock_supplier
            location_dest_id = picking_type.default_location_dest_id
        elif self.type == 'in_refund':
            location_id = picking_type.default_location_src_id
            location_dest_id = self.partner_id.property_stock_supplier
        elif self.type == 'out_invoice':
            location_id = picking_type.default_location_src_id
            location_dest_id = self.partner_id.property_stock_customer
        elif self.type == 'out_refund':
            location_id = self.partner_id.property_stock_customer
            location_dest_id = picking_type.default_location_dest_id
        return location_id, location_dest_id

    @api.multi
    def _prepare_stock_picking(self, picking_type, location_id, location_dest_id, origin, picking_date):
        vals= {
            'origin': origin,
            'picking_type_id': picking_type.id,
            'move_type': 'one',
            'partner_id': self.partner_id.id,
            'date': picking_date,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'invoice_ids': [(6, 0, self.ids)],
        }
        return vals 
    
    @api.multi
    def _process_message_picking_from_invoice(self, messages):
        #TODO: enviar notificacion con los mensajes encontrados
        if messages:
            raise UserError("\n".join(messages))
        return True
    
    @api.multi
    def _action_post_process_picking(self, picking):
        messages = []
        try:
            picking.action_confirm()
            picking.action_assign()
            picking.action_done()
        except Warning as e:
            #si hay errores al procesar el picking en el WF, capturar la excepcion y eliminar el picking
            messages.extend(e.message.split('\n'))
            picking.action_cancel()
            picking.write({'state':'draft'})
            picking.sudo().unlink()
            picking = False
        return picking, messages
    
    @api.multi
    def _action_create_picking(self):
        self.ensure_one()
        messages = []
        picking_model = self.env['stock.picking']
        picking = picking_model.browse()
        if not self.invoice_line_ids.filtered(lambda x: x.product_id and x.product_id.type != 'service'):
            messages.append('No hay lineas para mover inventario, por favor verifique')
        picking_type = self._get_stock_picking_type()
        location, location_dest = self._get_locations_from_picking(picking_type)
        if not location:
            if self.type == 'in_invoice':
                messages.append('Debe configurar la Ubicacion del Proveedor %s' % self.partner_id.name)
            else:
                messages.append('Debe configurar la Ubicacion de Stock en el Tipo de Operacion %s' % picking_type.name)
        if not location_dest:
            if self.type == 'in_invoice':
                messages.append('Debe configurar la Ubicacion de Stock en el Tipo de Operacion %s' % picking_type.name)
            else:
                messages.append('Debe configurar la Ubicacion del Cliente %s' % self.partner_id.name)
        if messages:
            return picking, messages
        picking_date = self._get_date_from_picking()
        origin = self.display_name
        picking = picking_model.create(self._prepare_stock_picking(picking_type, location.id, location_dest.id, origin, picking_date))
        self.invoice_line_ids.filtered(
            lambda l: l.product_id.type in ['product', 'consu']
            )._create_stock_moves(picking, location.id, location_dest.id, origin, picking_date)
        picking, messages = self._action_post_process_picking(picking)
        return picking, messages
    
    @api.multi
    def action_create_picking(self):
        for invoice in self.filtered('create_picking'):
            if invoice.picking_ids:
                continue
            picking, messages = invoice._action_create_picking()
            if messages:
                invoice._process_message_picking_from_invoice(messages)
        return True
    
    @api.multi
    def action_invoice_cancel(self):
        #si es factura que genero albaran, enviar a cancelar los albaranes relacionados
        picking_to_cancel = self.filtered('create_picking').mapped('picking_ids')
        if picking_to_cancel:
            picking_to_cancel.action_cancel()
        return super(account_invoice, self).action_invoice_cancel()
    
    @api.multi
    def action_invoice_draft(self):
        picking_to_unlink = self.filtered('create_picking').mapped('picking_ids')
        if picking_to_unlink:
            picking_to_unlink.write({'state':'draft'})
            picking_to_unlink.sudo().unlink()
        return super(account_invoice, self).action_invoice_draft()

class AccountInvoiceLine(models.Model):
    
    _inherit = 'account.invoice.line'
    
    @api.multi
    def get_price_unit_move(self):
        # para compras y NC de compras debe tomar el precio de la linea de factura
        # xq a ese precio se debe costear
        # para ventas o NC de ventas, debe tomar el precio de costo segun el despacho
        if self.invoice_id.type in ('in_invoice', 'in_refund'):
            price_unit = self.price_unit * (1 - (self.discount * 0.01))
            price_unit = self.uom_id._compute_price(price_unit, self.product_id.uom_id)
        else:
            price_unit = self._get_anglo_saxon_price_unit()
        return price_unit

    @api.multi
    def _prepare_stock_move(self, picking, location_id, location_dest_id, origin, picking_date):
        self.ensure_one()
        vals_move = {
            'name': self.name,
            'origin': origin,
            'product_id': self.product_id.id,
            'product_uom': self.uom_id.id,
            'product_uom_qty': self.quantity,
            'quantity_done': self.quantity,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'date': picking_date,
            'date_expected': picking_date,
            'picking_id': picking.id,
            'state': 'draft',
            'company_id': self.invoice_id.company_id.id,
            'price_unit': self.get_price_unit_move(),
            'picking_type_id': picking.picking_type_id.id,
            'warehouse_id': picking.picking_type_id.warehouse_id.id,
            'invoice_line_ids': [(6, 0, [self.id])],
        }
        quant_uom = self.product_id.uom_id
        get_param = self.env['ir.config_parameter'].sudo().get_param
        if self.uom_id.id != quant_uom.id and get_param('stock.propagate_uom') != '1':
            product_qty = self.uom_id._compute_quantity(self.quantity, quant_uom, rounding_method='HALF-UP')
            vals_move['product_uom'] = quant_uom.id
            vals_move['product_uom_qty'] = product_qty
        return vals_move

    @api.multi
    def _get_stock_moves_values(self, picking, location_id, location_dest_id, origin, picking_date):
        #devolver una lista de movimientos de stock a crear, 
        #por lo general sera un solo movimiento de stock x cada linea de factura
        #pero habra ocaciones donde se necesite crear mas de u movimiento de stock
        #Notas de credito por devolucion: el producto se deseche o se devuelva en buen estado
        vals_move = self._prepare_stock_move(picking, location_id, location_dest_id, origin, picking_date)
        return [vals_move]

    @api.multi
    def _create_stock_moves(self, picking, location_id, location_dest_id, origin, picking_date):
        moves = self.env['stock.move']
        done = moves.browse()
        for line in self:
            for vals in line._get_stock_moves_values(picking, location_id, location_dest_id, origin, picking_date):
                done |= moves.create(vals)
        return done
