import pytz
import xlsxwriter
from lxml import etree
from io import StringIO
from datetime import datetime

from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools.float_utils import float_round, float_compare

from odoo.addons.odoo_utils.models.report_formats import ReportFormats

STATES = {'draft': [('readonly', False)]}


class TransferRequisition(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'transfer.requisition'
    _description = 'Requisición de transferencia'
    _order = "name"
    
    name = fields.Char('Secuencial', readonly=True, copy=False)
    create_date = fields.Datetime('Fecha de Creación', readonly=True)
    create_uid = fields.Many2one('res.users', 'Creado por', readonly=True)
    requisition_date = fields.Datetime('Fecha de Solicitud', readonly=True, copy=False)
    requisition_uid = fields.Many2one('res.users', 'Solicitado por', readonly=True, copy=False)
    approved_date = fields.Datetime('Fecha de Aprobación', readonly=True, copy=False)
    approved_uid = fields.Many2one('res.users', 'Aprobado por', readonly=True, copy=False)
    received_date = fields.Datetime('Fecha de Recepción', readonly=True, copy=False)
    received_uid = fields.Many2one('res.users', 'Recibido por', readonly=True, copy=False)
    process_date = fields.Datetime('Fecha para Proceso', readonly=True,
        states={'draft': [('readonly', False)],  'request': [('readonly', False)]}, 
        help="Esta fecha es la que el sistema usará para realizar el movimiento de inventario, si usted desea usar la fecha actual deje el campo vacío",)
    backorder_id = fields.Many2one('transfer.requisition', 'Solicitud Anterior', readonly=True, copy=False)
    picking_type_origin_id = fields.Many2one('stock.picking.type', 'Origen', readonly=True, states=STATES,
        track_visibility='onchange')
    picking_type_dest_id = fields.Many2one('stock.picking.type', 'Destino', readonly=True, states=STATES,
        track_visibility='onchange')
    location_id = fields.Many2one('stock.location', 'Bodega Origen', readonly=True, states=STATES)
    location_dest_id = fields.Many2one('stock.location', 'Bodega Destino', readonly=True, states=STATES)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('request', 'Solicitado'),
        ('approved', 'Aprobado/Despachado'),
        ('process', 'Recibido'),
        ('done', 'Realizado'),
        ('cancel', 'Cancelado'),
        ],    string='Estado', index=True, readonly=True, default='draft',
        track_visibility='onchange')
    note = fields.Text(string='Observaciones', readonly=True, states=STATES)
    picking_ids = fields.One2many('stock.picking', 
        'transfer_requisition_dispatch_id', 'Transferencia(despacho)', readonly=True,
        context={'show_all_location': True})
    picking_dest_ids = fields.One2many('stock.picking', 
        'transfer_requisition_id', 'Transferencia(recepcion)', readonly=True,
        context={'show_all_location': True})
    picking_return_ids = fields.One2many('stock.picking', 
        'transfer_requisition_devolution_id', 'Transferencia(Devolucion)', readonly=True,
        context={'show_all_location': True})
    line_ids = fields.One2many('transfer.requisition.line', 
        'requisition_id', 'Lineas de Solicitud', 
        readonly=False, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    reason_ids = fields.One2many('transfer.requisition.reason', 'requisition_id', 'Razones', readonly=True)
    next_requisitions_ids = fields.One2many('transfer.requisition', 'backorder_id', 'Requisiones Dependientes')
    
    @api.model
    def get_groups_requisition_user(self):
        return ['stock_transfers.group_internal_transfer_user']
    
    @api.model
    def get_groups_requisition_approved(self):
        return ['stock_transfers.group_transfer_approved']
    
    @api.one
    @api.constrains('line_ids',)
    def _check_product_duplicity(self): 
        #validar que los productos no se repitan, sino no puedo validar stock
        product_data = {}
        for line in self.line_ids:
            product_data[line.product_id.id] = product_data.get(line.product_id.id, 0) +1
            if product_data[line.product_id.id] > 1:
                raise ValidationError(_("Los productos no pueden repetirse en las lineas a transferir, por favor verifique la linea con el producto %s") % (line.product_id.display_name))
    
    @api.one
    @api.constrains('location_id','location_dest_id')
    def _check_location_id(self): 
        if self.location_id.id == self.location_dest_id.id:
            raise ValidationError(_("La bodega origen y la bodega destino no pueden ser las mismas, por favor verifique"))
        
    @api.onchange('picking_type_origin_id',)
    def onchange_picking_type_origin(self):
        self.location_id = self.picking_type_origin_id.default_location_src_id.id
        
    @api.onchange('picking_type_dest_id',)
    def onchange_picking_type_dest(self):
        self.location_dest_id = self.picking_type_dest_id.default_location_dest_id.id
    
    @api.onchange('location_id', 'location_dest_id')
    def onchange_location_id(self):
        domain = {}
        warning={}
        from_origin = self.env.context.get('from_origin', False)
        if self.location_id and self.location_dest_id:
            #si las bodegas son iguales, advertir al usuario
            if self.location_id == self.location_dest_id:
                warning['title'] = 'Información para el usuario'
                warning['message'] = 'La bodega origen y la bodega destino no pueden ser las mismas, por favor verifique'
                if from_origin:
                    self.location_id = False
                else:
                    self.location_dest_id = False
        return {'domain': domain, 'warning' : warning }
    
    @api.model
    def _is_user_approved(self):
        user_model = self.env['res.users']
        return any([user_model.has_group(group_id_xml) for group_id_xml in self.get_groups_requisition_approved()])
    
    @api.model
    def _is_user_received(self):
        user_model = self.env['res.users']
        return any([user_model.has_group(group_id_xml) for group_id_xml in self.get_groups_requisition_user()])
    
    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        def set_attr(attr, field_name, value="1", class_type='field'):
            nodes = doc.xpath("//%s[@name='%s']" % (class_type,field_name))
            for node in nodes:
                node.set(attr, value)
        res = super(TransferRequisition, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        util_model = self.env['odoo.utils']
        if view_type == 'form':
            if 'line_ids' in res['fields']:
                for view in res['fields']['line_ids']['views']:
                    doc = etree.XML(res['fields']['line_ids']['views'][view]['arch'])
                    modifiers = {'readonly': True, 'attrs': {}}
                    #modificar los campos segun el usuario que este viendo el registro
                    #si es aprobador, permitir modificar las cantidades a procesar solo a ese grupo
                    #si es solicitante, permitir modificar las cantidades recibidas solo a ese grupo
                    if 'qty_process' in res['fields']['line_ids']['views'][view]['fields'] and not self._is_user_approved():
                        util_model.find_set_node(doc, 'qty_process', modifiers)
                    if 'qty_received' in res['fields']['line_ids']['views'][view]['fields'] and not self._is_user_received():
                        util_model.find_set_node(doc, 'qty_received', modifiers)
                    res['fields']['line_ids']['views'][view]['arch'] = etree.tostring(doc)
        return res
    
    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('transfer.requisition')
        new_rec = super(TransferRequisition, self).create(vals)
        return new_rec
    
    @api.multi
    def write(self, vals):
        #TODO: process before updating resource
        res = super(TransferRequisition, self).write(vals)
        if 'state' in vals:
            for transfer in self:
                if transfer.line_ids:
                    transfer.line_ids.write({'state': vals['state']})
        return res
    
    @api.multi
    def unlink(self):
        Pickings = self.env['stock.picking']
        picking_recs = Pickings.browse() 
        for requisition in self:
            if requisition.state not in ('draft','cancel'):
                raise UserError(_("No puede eliminar este registro, intente cancelarlo primero"))
            picking_recs |= requisition.picking_ids
            picking_recs |= requisition.picking_dest_ids
            picking_recs |= requisition.picking_return_ids
        if picking_recs:
            picking_recs.write({'state': 'draft'})
            picking_recs.unlink()
        return super(TransferRequisition, self).unlink()
    
    @api.multi
    def name_get(self):
        res = []
        for transfer in self:
            name = "%s(Origen: %s. Destino: %s." % (transfer.name, transfer.location_id.display_name, transfer.location_dest_id.display_name)
            res.append((transfer.id, name))
        return res
    
    @api.multi
    def _validate_qty_process(self):
        """Validar que las cantidades aprobadas esten en stock disponible
        """
        ctx = self.env.context.copy()
        ctx2 = self.env.context.copy()
        messajes = []
        for requisition in self:
            ctx['location'] = requisition.location_id.id
            ctx['show_all_stock'] = True
            for line in requisition.line_ids:
                if not line.to_process:
                    continue
                qty_available =  line.product_id.with_context(ctx)._compute_quantities_dict(ctx.get('lot_id'), ctx.get('owner_id'), ctx.get('package_id'), ctx.get('from_date'), ctx.get('to_date'))[line.product_id.id]['qty_available']
                #como la udm puede ser diferente a la del producto, pasar la cantidad disponible a la udm de venta
                if line.uom_id.id != line.product_id.uom_id.id:
                    ctx2['product_id_comp_uom'] = line.product_id.id
                    qty_available = line.product_id.uom_id._compute_quantity(qty_available, line.uom_id)
                if qty_available < line.qty_process:
                    if self.env.context.get('transfer_from_pos'):
                        messajes.append("***Producto: %s Cantidad Requerida: %s %s Cantidad Disponible: %s %s Bodega: %s" % 
                                        (line.product_id.display_name, line.qty_process, line.uom_id.name, qty_available, line.uom_id.name, requisition.location_id.display_name))
                    else:
                        messajes.append((0,0,{
                            'product_id': line.product_id.id,
                            'product_qty': line.qty_process,
                            'qty_available': qty_available,
                            'uom_id': line.uom_id.id,
                            'location_id': requisition.location_id.id,
                        }))
        if messajes and self.env.context.get('transfer_from_pos'):
            raise UserError("Los siguientes productos no tienen stock suficiente, por favor verifique antes de continuar.\n" + "\n".join(messajes))
        return messajes
    
    @api.multi
    def check_lines(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("No hay lineas a solicitar"))
        return True
            
    @api.multi
    def action_request(self):
        seq_model = self.env['ir.sequence']
        company = self.env.user.company_id
        for requisition in self:
            requisition.check_lines()
            if not requisition.name:
                requisition.write({'name': seq_model.next_by_code('transfer.requisition')})
            requisition.write({
                'requisition_uid': self.env.uid,
                'requisition_date': datetime.now(),
            })
        if company.internal_transfer_steps == '2_step':
            for requisition in self:
                for line in requisition.line_ids:
                    line.write({
                        'qty_process': line.product_qty,
                        'to_process': True,
                    })
            #validar las cantidades a solicitar/aprobar(cuando la solicitud y aprobacion se hace en el mismo paso
            if company.stock_policy == 'control_stock' or self.env.context.get('force_validation_stock'):
                res = self._action_check_stock()
                if not res is True:
                    return res
        self.write({'state': 'request'})
        if company.internal_transfer_steps == '2_step':
            return self._action_approved()
        return True
    
    @api.model
    def _get_lines_changed(self, requisition, field_comp1='product_qty', field_comp2 = 'qty_process'):
        """
        Verifica si las lineas se estan aprobando con las cantidades solicitadas o hay diferencias
        Si hay diferencias el usuario debe especificar que hacer con esa diferencia
        @return: tuple(lineas_normales, lineas_con_diferencia)
        """
        line_normal_ids, line_diff_ids = [], []
        for line in requisition.line_ids:
            if not line.to_process:
                continue
            vals = {
                'line_id': line.id,
                'product_id': line.product_id.id,
                field_comp1: line[field_comp1],
                field_comp2: line[field_comp2],
                'qty_diff': line[field_comp2] - line[field_comp1],
                'process_type': 'normal',
            }
            #el campo process_mode solo se debe pasar cuando el  field_comp1 != 'product_qty'
            #ya que esta funcion trabaja sobre dos asistentes, el campo process_mode solo existe en uno de ellos y en el otro no
            if field_comp1 != 'product_qty':
                vals['process_mode'] = 'deterioro' if line[field_comp1] > line[field_comp2] else ''
            if line[field_comp1] != line[field_comp2]:
                vals['process_type'] = 'diff'
                line_diff_ids.append(vals)
            else:
                line_normal_ids.append(vals)
        if not line_normal_ids and not line_diff_ids:
            raise UserError(_("Debe Seleccionar las lineas a procesar"))
        return line_normal_ids, line_diff_ids
    
    @api.multi
    def _action_check_stock(self):
        #validar las cantidades a procesar
        util_model = self.env['odoo.utils']
        wizard_model = self.env['wizard.product.no.stock']
        message_line_ids = self._validate_qty_process()
        if message_line_ids:
            wizard_rec = wizard_model.create({'line_ids': message_line_ids})
            res = util_model.show_wizard(wizard_model._name, 'wizard_product_no_tock_form_view', 'Productos sin Stock')
            res['res_id'] = wizard_rec.id
            return res
        return True
    
    @api.multi
    def _action_approved(self):
        #validar las cantidades a procesar
        company = self.env.user.company_id
        if company.internal_transfer_steps == '3_step':
            if company.stock_policy == 'control_stock' or self.env.context.get('force_validation_stock'):
                res = self._action_check_stock()
                if not res is True:
                    return res
        picking_model = self.env['stock.picking']
        picking_recs = picking_model.browse()
        company = self.env.user.company_id
        transfer_auto_validate_picking = company.transfer_auto_validate_picking
        location_transfer = company.internal_transit_location_id
        for requisition in self:
            picking_recs = picking_model.browse()
            lines_to_process = requisition.line_ids.filtered('to_process')
            lines_no_process = requisition.line_ids - lines_to_process
            if lines_to_process:
                picking = requisition._make_picking(requisition.picking_type_origin_id, requisition.location_id, location_transfer, requisition.name, requisition.process_date)
                picking_recs |= picking
                for line in lines_to_process:
                    self._make_move_approved(line, picking, requisition.location_id, location_transfer, company)
            if lines_no_process:
                #si no se aprobo, pasar la cantidad a 0
                lines_no_process.write({'qty_process': 0})
            if picking_recs:
                picking_recs.action_confirm()
                picking_recs.action_assign()
                if transfer_auto_validate_picking:
                    picking_recs.action_done()
        self.write({
            'state': 'approved',
            'approved_uid': self.env.uid,
            'approved_date': datetime.now(),
        })
        return True 
                
    @api.multi
    def action_approved(self):
        #verificar si hay lineas que se modifico la cantidad aprobada
        util_model = self.env['odoo.utils']
        line_normal_ids, line_diff_ids = self._get_lines_changed(self)
        #si hay diferencias, mostrar asistente para que usuario indique como proceder con las diferencias
        ctx = self.env.context.copy()
        ctx['active_model'] = self._name
        ctx['active_ids'] = self.ids
        ctx['active_id'] = self.ids and self.ids[0] or False
        #solo cuando apruebe menos de lo solicitado 
        #se debe levantar asistente para preguntar si se crea otra solicitud por las diferencias
        has_remaining = False
        for line in line_diff_ids:
            if line['qty_diff'] < 0.0:
                has_remaining = True
                break 
        if has_remaining:
            res = util_model.with_context(ctx).show_wizard('wizard.approved.transfer.requisition', 'wizard_approved_transfer_requisition_form_view', _('Aprobar Solicitud de Transferencia'))
        else:
            res = self._action_approved()
        return res
    
    @api.multi
    def action_mark_qty(self):
        # pasar la cantidad aprobada como la cantidad a recibir
        # solo para facilitar el ingreso de datos de parte del usuario
        for transfer in self:
            for line in transfer.line_ids:
                line.write({'qty_received': line.qty_process})
        return True
    
    @api.multi
    def action_mark_no_qty(self):
        # pasar la cantidad a recibir en 0 
        # solo para facilitar el ingreso de datos de parte del usuario
        for transfer in self:
            transfer.line_ids.write({'qty_received': 0})
        return True
    
    @api.multi
    def _prepare_stock_picking(self, picking_type, location, location_dest, origin, picking_date, internal_type):
        '''
        @param internal_type: indica si es el picking de despacho o recepcion, solo soporta esos 2 posibles valores
        @return: dict con los valores para crear el picking
        '''
        vals= {
            'origin': origin,
            'note': origin,
            'picking_type_id': picking_type.id,
            'move_type': 'one',
            'location_id': location.id,
            'location_dest_id': location_dest.id,
        }
        if picking_date:
            vals['date_movement'] = picking_date
        return vals
    
    @api.multi
    def _make_picking(self, picking_type, location, location_dest, origin, picking_date):
        picking_vals = self._prepare_stock_picking(picking_type, location, location_dest, origin, picking_date, 'dispatch')
        picking_vals['transfer_requisition_dispatch_id'] = self.id
        picking =  self.env['stock.picking'].create(picking_vals)
        return picking
    
    @api.multi
    def _make_picking_aditional(self, picking_type, location, location_dest, origin, picking_date):
        picking_vals = self._prepare_stock_picking(picking_type, location, location_dest, origin, picking_date, 'dispatch_aditional')
        picking_vals['transfer_requisition_dispatch_id'] = self.id
        picking_vals['note'] += " Adicional"
        picking =  self.env['stock.picking'].create(picking_vals)
        return picking
    
    @api.multi
    def _make_picking_dest(self, picking_type, location, location_dest, origin, picking_date):
        picking_vals = self._prepare_stock_picking(picking_type, location, location_dest, origin, picking_date, 'reception')
        picking_vals['transfer_requisition_id'] = self.id
        picking =  self.env['stock.picking'].create(picking_vals)
        return picking
    
    @api.model
    def _get_vals_move(self, line, picking, location, location_dest):
        requisition = line.requisition_id
        date_move = datetime.now()
        vals = {
            'name': requisition.name + ': ' + line.product_id.display_name,
            'product_id': line.product_id.id,
            'product_uom_qty': line.product_qty,
            'product_uom': line.uom_id.id,
            'date': date_move,
            'date_expected': date_move,
            'location_id': location.id,
            'location_dest_id': location_dest.id,
            'state': 'draft',
            'price_unit': line.product_id.standard_price, #pasar el precio en la UdM del producto, no usar la conversion
            'picking_id': picking.id,
        }
        return vals
    
    @api.model
    def _make_move_approved(self, line, picking, location, location_dest, company):
        move_model = self.env['stock.move']
        move_recs = move_model.browse()
        vals = self._get_vals_move(line, picking, location, location_dest)
        vals['product_uom_qty'] = line.qty_process
        vals['transfer_requisition_line_dispatch_id'] = line.id
        if company.transfer_auto_validate_picking:
            vals['quantity_done'] = line.qty_process
        if vals.get('product_uom_qty', 0.0) != 0.0:
            move_recs += move_model.create(vals)
        return move_recs
    
    @api.model
    def _make_move_approved_aditional(self, line, picking, location, location_dest, company):
        move_model = self.env['stock.move']
        move_recs = move_model.browse()
        vals = self._get_vals_move(line, picking, location, location_dest)
        quantity = float_round(line.qty_received - line.qty_process, precision_rounding=line.uom_id.rounding)
        vals['product_uom_qty'] = quantity
        vals['transfer_requisition_line_dispatch_id'] = line.id
        if company.transfer_auto_validate_picking:
            vals['quantity_done'] = quantity
        if vals.get('product_uom_qty', 0.0) != 0.0:
            move_recs += move_model.create(vals)
        return move_recs
    
    @api.model
    def _make_move_received(self, line, picking, location, location_dest, company):
        move_model = self.env['stock.move']
        move_recs = move_model.browse()
        vals = self._get_vals_move(line, picking, location, location_dest)
        vals['product_uom_qty'] = line.qty_received
        vals['transfer_requisition_line_id'] = line.id
        if line.move_ids:
            vals['move_orig_ids'] = [(6, 0, line.move_ids.ids)]
        if company.transfer_auto_validate_picking:
            vals['quantity_done'] = line.qty_received
            # cuando se recibe menos pero se configura que la diferencia debe quedar como recepcion parcial
            # pasar la cantidad apobada al campo cantidad planificada
            if company.internal_transfer_partial_reception == 'create_backorder':
                vals['product_uom_qty'] = line.qty_process
        if vals.get('product_uom_qty', 0.0) != 0.0:
            move_recs += move_model.create(vals)
        return move_recs
    
    @api.multi
    def _action_receive(self):
        picking_model = self.env['stock.picking']
        picking_recs = picking_model.browse()
        company = self.env.user.company_id
        transfer_auto_validate_picking = company.transfer_auto_validate_picking
        location_transfer = company.internal_transit_location_id
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for requisition in self.with_context(show_all_location=True):
            if requisition.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel')):
                raise UserError(u"No se puede recibir ya que los despachos no se han procesado, por favor verifique")
            picking_recs = picking_model.browse()
            picking_aditional_recs = picking_model.browse()
            lines_to_process = requisition.line_ids.filtered(lambda x: x.to_process and x.qty_received)
            lines_no_process = requisition.line_ids - lines_to_process
            lines_to_process_aditional = lines_to_process.filtered(lambda x: float_compare(x.qty_received, x.qty_process, precision_digits=precision) > 0)
            if lines_to_process_aditional:
                # si se esta recibiendo mas de lo despachado, se debe crear otro picking por la diferencia
                # para que el stock se de de baja en la bodega origen
                picking_aditional_recs = requisition._make_picking_aditional(requisition.picking_type_origin_id, requisition.location_id, location_transfer, requisition.name, requisition.process_date)
                for line in lines_to_process_aditional:
                    self._make_move_approved_aditional(line, picking_aditional_recs, requisition.location_id, location_transfer, company)
                if picking_aditional_recs:
                    message = _("Se creo un picking adicional <a href=# data-oe-model=stock.picking data-oe-id=%d>%s</a>") % (picking_aditional_recs.id, picking_aditional_recs.display_name)
                    requisition.message_post(body=message)
                    picking_aditional_recs.action_confirm()
                    picking_aditional_recs.action_assign()
                    if transfer_auto_validate_picking:
                        picking_aditional_recs.action_done()
            if lines_to_process:
                picking = requisition._make_picking_dest(requisition.picking_type_dest_id, location_transfer, requisition.location_dest_id, requisition.name, requisition.process_date)
                picking_recs |= picking
                for line in lines_to_process:
                    self._make_move_received(line, picking, location_transfer, requisition.location_dest_id, company)
            if lines_no_process:
                #si no se aprobo, pasar la cantidad a 0
                lines_no_process.write({'qty_received': 0})
            if picking_recs:
                picking_recs.action_confirm()
                picking_recs.action_assign()
                if transfer_auto_validate_picking:
                    picking_recs.action_done()
            requisition._action_devolution()
        self.write({
            'state': 'process',
            'received_uid': self.env.uid,
            'received_date': datetime.now(),
        })
        self.action_done()
        return True
    
    @api.multi
    def _action_devolution(self):
        for requisition in self:
            product_received_more = {}
            for picking in requisition.picking_ids.filtered(lambda x: x.state == 'done'):
                product_return_moves = []
                for move in picking.move_lines:
                    quantity = move.product_qty
                    quantity_received = 0.0
                    qty_dest = 0.0
                    move_dest_ids = move.move_dest_ids.filtered(lambda m: m.state in ['partially_available', 'assigned', 'done'])
                    for move_dest in move_dest_ids:
                        if move_dest.state == 'done':
                            qty_dest = sum(move_dest.mapped('move_line_ids').mapped('qty_done'))
                        else:
                            qty_dest = sum(move_dest.mapped('move_line_ids').mapped('product_qty'))
                        quantity -= qty_dest
                        quantity_received += qty_dest
                    quantity = float_round(quantity, precision_rounding=move.product_uom.rounding)
                    # la  devolucion se debe hacer cuando se reciba menos de lo que se despacho
                    # pero cuando se reciba mas de lo despachado, no deberria permitirse 
                    # ya que el stock nunca se rebajaria en la bodega origen, este sale de la bodega de transito
                    if quantity > 0.0:
                        product_return_moves.append((0, 0, {'product_id': move.product_id.id, 'quantity': quantity, 'move_id': move.id, 'uom_id': move.product_id.uom_id.id}))
                    elif quantity < 0.0:
                        if move.product_id.id not in product_received_more:
                            product_received_more[move.product_id.id] = True
                            message = "Se recibio mas cantidad de la despachada en el Producto %s, Cantidad despachada: %s Cantidad recibida: %s" % \
                                (move.product_id.display_name, move.product_qty, quantity_received)
                            requisition.message_post(body=message)
                if product_return_moves:
                    ctx = self.env.context.copy()
                    ctx['active_model'] = 'stock.picking'
                    ctx['active_id'] = picking.id
                    ctx['active_ids'] = picking.ids
                    ReturnModel = self.env['stock.return.picking'].with_context(ctx)
                    ReturnWizard = ReturnModel.create({'product_return_moves': product_return_moves})
                    new_picking_id, picking_type_id = ReturnWizard._create_returns()
                    message = _("Se creo la devolucion <a href=# data-oe-model=stock.picking data-oe-id=%d>%s</a>") % (new_picking_id, self.env['stock.picking'].browse(new_picking_id).display_name)
                    requisition.message_post(body=message)
        return True
        
    
    @api.multi
    def action_process(self):
        #verificar si hay lineas que se modifico la cantidad aprobada
        util_model = self.env['odoo.utils']
        line_normal_ids, line_diff_ids = self._get_lines_changed(self, 'qty_process', 'qty_received')
        #si hya diferencias, mostrar asistente para que usuario indique como proceder con las diferencias
        ctx = self.env.context.copy()
        ctx['active_model'] = self._name
        ctx['active_ids'] = self.ids
        ctx['active_id'] = self.ids and self.ids[0] or False
        if line_diff_ids:
            res = util_model.with_context(ctx).show_wizard('wizard.received.transfer.requisition', 'wizard_received_transfer_requisition_form_view', _('Recibir Transferencia'))
        else:
            res = self._action_receive()
        return res
    
    @api.multi
    def action_done(self):
        self.write({'state': 'done'})
        return True
    
    @api.multi
    def action_cancel(self):
        Pickings = self.env['stock.picking']
        picking_recs = Pickings.browse() 
        for requisition in self:
            picking_recs |= requisition.picking_ids
            picking_recs |= requisition.picking_dest_ids
            picking_recs |= requisition.picking_return_ids
            if requisition.next_requisitions_ids:
                requisition.next_requisitions_ids.action_cancel()
        if picking_recs:
            picking_recs.with_context(force_cancel_picking=True).action_cancel()
        self.write({'state': 'cancel'})
        return True

    @api.multi
    def action_cancel_to_draft(self):
        Pickings = self.env['stock.picking']
        picking_recs = Pickings.browse() 
        for requisition in self:
            picking_recs |= requisition.picking_ids
            picking_recs |= requisition.picking_dest_ids
            picking_recs |= requisition.picking_return_ids
            requisition.line_ids.write({
                'qty_process': 0.0,
                'qty_received': 0.0,
                'to_process': False,
            })
        if picking_recs:
            picking_recs.write({'state': 'draft'})
            picking_recs.unlink()
        self.write({'state': 'draft'})
        return True

    @api.multi
    def action_print_report(self):
        return self.env['report'].get_action(self, 'stock_transfers.report_transfer_requisition')
        
    @api.multi
    def action_mark_lines(self):
        checked = self.env.context.get('lines_marked', False)
        for requisition in self:
            if requisition.line_ids:
                requisition.line_ids.write({'to_process': checked})
        return True
    
    @api.model
    def get_lines_for_report_analisis(self, time_zone_pg="AT TIME ZONE 'UTC'"):
        product_ids = self.env.context.get('product_ids', [])
        location_ids = self.env.context.get('location_ids', [])
        location_source_ids = self.env.context.get('location_source_ids', [])
        user_ids = self.env.context.get('user_ids', [])
        date_start = self.env.context.get('date_start', False)
        date_end = self.env.context.get('date_end', False)
        to_process = self.env.context.get('to_process', False)
        where_str = ["l.state NOT IN ('draft', 'cancel')"]
        where_str.append("(l.product_qty > 0 OR l.qty_process > 0)")
        params = {}
        if to_process:
            where_str.append("l.to_process = true")
        if product_ids:
            where_str.append("l.product_id IN %(product_ids)s")
            params['product_ids'] = tuple(product_ids)
        if location_ids and location_source_ids:
            where_str.append(" (l.location_dest_id IN %(location_ids)s OR l.location_id IN %(location_source_ids)s)")
            params['location_ids'] = tuple(location_ids)
            params['location_source_ids'] = tuple(location_source_ids)
        else:
            if location_ids:
                where_str.append("l.location_dest_id IN %(location_ids)s")
                params['location_ids'] = tuple(location_ids)
            if location_source_ids:
                where_str.append("l.location_id IN %(location_source_ids)s")
                params['location_source_ids'] = tuple(location_source_ids)
        #TODO: filtrar que usuario: solicita, aprueba o recibe???
        if user_ids:
            where_str.append("l.requisition_uid IN %(user_ids)s")
            params['user_ids'] = tuple(user_ids)
        #TODO: por que fecha filtrar?
        if date_start:
            where_str.append("l.process_date >= %(date_start)s")
            params['date_start'] = date_start
        if date_end:
            where_str.append("l.process_date <= %(date_end)s")
            params['date_end'] = date_end
        SQL = """
            SELECT l.name AS name, l.state AS state, w.name AS shop,
                lo.name AS location, ld.name AS location_dest,
                p.default_code AS default_code, pt.name AS product, um.name AS uom,
                l.product_qty, l.qty_process, l.qty_received, l.price_unit,
                part_req.name AS requisition_uid, TO_CHAR(l.process_date """ + time_zone_pg + """, 'YYYY-MM-DD HH24:MI:SS') AS process_date,
                part_app.name AS approved_uid, TO_CHAR(l.approved_date """ + time_zone_pg + """, 'YYYY-MM-DD HH24:MI:SS') AS approved_date,
                part_rec.name AS received_uid, TO_CHAR(l.received_date """ + time_zone_pg + """, 'YYYY-MM-DD HH24:MI:SS') AS received_date
            FROM transfer_requisition_report_analisis l
                INNER JOIN product_product p ON p.id = l.product_id
                INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
                INNER JOIN stock_warehouse w ON w.id = l.warehouse_id
                INNER JOIN stock_location lo ON lo.id = l.location_id
                INNER JOIN stock_location ld ON ld.id = l.location_dest_id
                INNER JOIN product_uom um ON um.id = l.uom_id
                LEFT JOIN res_users user_req ON user_req.id = l.requisition_uid
                LEFT JOIN res_partner part_req ON part_req.id = user_req.partner_id 
                LEFT JOIN res_users user_app ON user_app.id = l.approved_uid
                LEFT JOIN res_partner part_app ON part_app.id = user_app.partner_id
                LEFT JOIN res_users user_rec ON user_rec.id = l.received_uid
                LEFT JOIN res_partner part_rec ON part_rec.id = user_rec.partner_id
            """ + ((" WHERE %s" % (" AND ".join(where_str))) if where_str else "") + """
            ORDER BY process_date, w.name, pt.name
        """
        
        self.env.cr.execute(SQL, params)
        return self.env.cr.dictfetchall()
    
    @api.model
    def MakeReportTransfer(self):
        util_model = self.env['odoo.utils']
        fields_model = self.env['ir.fields.converter']
        tz_name = fields_model._input_tz()
        transfer_lines = self.get_lines_for_report_analisis()
        date_start = self.env.context.get('date_start', False)
        date_end = self.env.context.get('date_end', False)
        start_date_tz, end_date_tz = "", ""
        dates_string = ""
        if date_start:
            start_date_tz = util_model._change_time_zone(datetime.strptime(date_start, DTF), pytz.UTC, tz_name)
            dates_string += " desde %s" % (start_date_tz.strftime(DTF))
        if date_end:
            end_date_tz = util_model._change_time_zone(datetime.strptime(date_end, DTF), pytz.UTC, tz_name)
            dates_string += " hasta %s" % (end_date_tz.strftime(DTF))
        fp = StringIO()
        #crear el reporte en memoria, no en archivo
        workbook = xlsxwriter.Workbook(fp, {'in_memory': True, 'constant_memory': True})
        report_format = ReportFormats(workbook)
        sheet_name = 'Transferencias'
        worksheet = workbook.add_worksheet(sheet_name)
        FIELDS_SHOW = [
            'name',
            'shop',
            'location',
            'location_dest',
            'default_code',
            'product',
            'product_qty',
            'qty_process',
            'qty_received',
            'uom',
            'price_unit',
            'requisition_uid',
            'process_date',
            'approved_uid',
            'approved_date',
            'received_uid',
            'received_date',
        ]
        #generar una posicion segun el orden que aparecen en la lista
        #para que en caso de querer cambiar la posicion de un campo, solo moverlo en la lista
        #y no tener que estar recalculando posiciones manualmente
        COLUM_POS = dict([(f,i) for i, f in enumerate(FIELDS_SHOW)])
        COLUM_SIZE = {
            'name': 12,
            'shop': 25,
            'location': 15,
            'location_dest': 15,
            'default_code': 15,
            'product': 25,
            'product_qty': 12,
            'qty_process': 12,
            'qty_received': 12,
            'uom': 12,
            'price_unit': 12,
            'requisition_uid': 20,
            'process_date': 17,
            'approved_uid': 20,
            'approved_date': 17,
            'received_uid': 20,
            'received_date': 17,
        }
        COLUM_HEADER = {
            'name': 'Solicitud Nº',
            'shop': 'Almacen',
            'location': 'Bodega Origen',
            'location_dest': 'Bodega Destino',
            'default_code': 'Codigo',
            'product': 'Producto',
            'product_qty': 'Cant. Solicitada',
            'qty_process': 'Cant. Aprobada',
            'qty_received': 'Cant. Recibida',
            'uom': 'UdM',
            'price_unit': 'Precio Unitario',
            'requisition_uid': 'Solicitado por',
            'process_date': 'Fecha de proceso',
            'approved_uid': 'Aprobado por',
            'approved_date': 'Fecha de aprobacion',
            'received_uid': 'Recibido por',
            'received_date': 'Fecha de recepción',
        }
        COLUM_FORMAT = {
            'name': False,
            'shop': False,
            'location': False,
            'location_dest': False,
            'default_code': False,
            'product': False,
            'product_qty': 'number',
            'qty_process': 'number',
            'qty_received': 'number',
            'uom': False,
            'price_unit': 'money',
            'requisition_uid': False,
            'process_date': 'datetime',
            'approved_uid': False,
            'approved_date': 'datetime',
            'received_uid': False,
            'received_date': 'datetime',
        }
        current_row = 0
        worksheet.freeze_panes(2,0)
        worksheet.merge_range(current_row, 0, current_row, 4, 
                              "Transferencias %s" % dates_string, report_format.GetFormat('merge_center'))
        current_row += 1
        for key, value in COLUM_HEADER.items():
            worksheet.write(current_row, COLUM_POS[key], value, report_format.GetFormat('bold'))
        current_row += 1
        for line in transfer_lines:
            for field_name in FIELDS_SHOW:
                worksheet.write(current_row, COLUM_POS[field_name], line.get(field_name, ''), report_format.GetFormat(COLUM_FORMAT[field_name]))
            current_row += 1
        #ancho de columnas
        for column_name, position in COLUM_POS.items():
            worksheet.set_column(position, position, COLUM_SIZE[column_name])
        workbook.close()
        fp.seek(0)
        data = fp.read()
        fp.close()
        return data

class TransferRequisitionLine(models.Model):

    _name = 'transfer.requisition.line'
    _description = 'Lineas de transferencia'
    _rec_name = 'requisition_id'
    
    requisition_id = fields.Many2one('transfer.requisition', 'Solicitud', required=False, ondelete="cascade")
    product_id = fields.Many2one('product.product', 'Producto', required=False, save_readonly=True, ondelete="restrict")
    uom_id = fields.Many2one('uom.uom', 'UdM', required=False, save_readonly=True)
    product_qty = fields.Float('Cantidad Solicitada', digits=dp.get_precision('Product Unit of Measure'), save_readonly=True)
    qty_process = fields.Float('Cantidad Procesada', digits=dp.get_precision('Product Unit of Measure'), save_readonly=True)
    qty_received = fields.Float('Cantidad Recibida', digits=dp.get_precision('Product Unit of Measure'), save_readonly=True)
    price_unit = fields.Float('Precio Unitario', digits=dp.get_precision('Purchase Price'), readonly=True, save_readonly=True)
    to_process = fields.Boolean('A procesar?', readonly=False, save_readonly=True)
    reason = fields.Text(string='Razón', required=False)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('request', 'Solicitado'),
        ('approved', 'Aprobado'),
        ('process', 'Enviado/Despachado'),
        ('done', 'Realizado'),
        ('cancel', 'Cancelado'),
    ],    string='Estado', index=True, readonly=True)
    process_mode = fields.Selection([
        ('perdida','Pérdida'),
        ('robo','Robo'),
        ('deterioro','Deterioro'),
        ('ingreso_extra','Ingresos Extra'),
        ],    string='Diferencias dadas por', index=True)
    move_ids = fields.One2many('stock.move', 'transfer_requisition_line_dispatch_id', u'Movimientos de despacho', readonly=True,
        context={'show_all_location': True})
    
    @api.one
    @api.constrains('product_id','uom_id')
    def _check_product_uom(self): 
        if self.product_id.uom_id.category_id.id != self.uom_id.category_id.id:
            raise ValidationError(_("La unidad de medida seleccionada debe pertenecer a la misma categoría que la unidad de medida del producto: %s") % self.product_id.display_name)
    
    @api.one
    @api.constrains('product_qty',)
    def _check_product_qty(self): 
        if self.product_qty < 0.0:
            raise ValidationError(_("La cantidad a transferir debe ser mayor a cero, por favor verifique la linea con el producto %s") % self.product_id.display_name)
    
    @api.one
    @api.constrains('qty_process',)
    def _check_qty_process(self): 
        if self.qty_process < 0.0:
            raise ValidationError(_("La cantidad Procesada debe ser mayor a cero, por favor verifique la linea con el producto %s") % self.product_id.display_name)
    
    @api.one
    @api.constrains('qty_received',)
    def _check_qty_received(self): 
        if self.qty_received < 0.0:
            raise ValidationError(_("La cantidad a Recibida debe ser mayor a cero, por favor verifique la linea con el producto %s") % self.product_id.display_name)
    
    @api.onchange('product_id',)
    def onchange_product_id(self):
        domain = {}
        warning={}
        if not self.requisition_id.location_id:
            self.product_id = False
            domain['uom_id'] = []
            warning = {'title': 'Advertencia',
                       'message': 'Debe seleccionar la bodega Origen'
                       }
            return {'domain': domain, 'warning' : warning }
        if not self.product_id:
            self.uom_id = False
            self.price_unit = 0.0
            domain['uom_id'] = []
            return {'domain': domain, 'warning' : warning }
        self.uom_id = self.product_id.uom_id.id
        self.price_unit = self.product_id.standard_price
        domain['uom_id'] = [('category_id','=',self.product_id.uom_id.category_id.id)]
        return {'domain': domain, 'warning' : warning }
    
    @api.model
    def _validate_qty_available(self, product_qty_validate):
        messages = []
        ctx = self.env.context.copy()
        ctx2 = self.env.context.copy()
        ctx2['product_id_comp_uom'] = self.product_id.id
        #validar si hay stock
        #como la udm puede ser diferente a la del producto, pasar la cantidad disponible a la udm de venta
        if not self.env.context.get('skip_validation_stock', False):
            ctx['location'] = self.requisition_id.location_id.id
            ctx['show_all_stock'] = True
            qty_available =  self.product_id.with_context(ctx)._compute_quantities_dict(ctx.get('lot_id'), ctx.get('owner_id'), ctx.get('package_id'), ctx.get('from_date'), ctx.get('to_date'))[self.product_id.id]['qty_available']
            if self.uom_id.id != self.product_id.uom_id.id:
                qty_available = self.product_id.uom_id._compute_quantity(qty_available, self.uom_id)
            if qty_available < product_qty_validate:
                product_qty = qty_available
                if qty_available > 0:
                    messages.append(_('No hay suficiente stock para el producto %s, solo puede Transferir %s %s') % (self.product_id.display_name, qty_available, self.uom_id.name))
                else:
                    messages.append(_('No hay stock disponible para el producto %s') % (self.product_id.display_name))
                    product_qty = 0.0
                if self.requisition_id.state == 'request':
                    self.qty_process = product_qty
                else:
                    self.product_qty = product_qty
        return messages
    
    @api.onchange('product_qty', 'qty_process', 'uom_id')
    def onchange_product_qty(self):
        domain = {}
        warning={}
        messages = []
        company = self.env.user.company_id
        requisition = self.requisition_id
        product_qty_validate = self.product_qty
        #cuando este aprobando, la cantidad a validar es la cantidad a aprobar
        if requisition.state == 'request':
            product_qty_validate = self.qty_process
        #la validacion se hace a nivel de constraints pero advertirle al usuario de inmediato
        if product_qty_validate < 0:
            warning = {'title': 'Error',
                       'message': 'La cantidad a transferir no puede ser negativa, por favor corrija',
                       }
            return {'domain': domain, 'warning' : warning }
        if not self.requisition_id.location_id:
            warning = {'title': 'Advertencia',
                       'message': 'Debe seleccionar la bodega Origen',
                       }
            return {'domain': domain, 'warning' : warning }
        if not self.product_id:
            domain['uom_id'] = []
            return {'domain': domain, 'warning' : warning }
        if not self.uom_id:
            warning = {'title': 'Información',
                       'message': 'Debe seleccionar la Unidad de medida',
                       }
            return {'domain': domain, 'warning' : warning }
        if self.product_id and self.requisition_id.location_id and self.uom_id:
            domain['uom_id'] = [('category_id','=',self.product_id.uom_id.category_id.id)]
            if self.product_id.uom_id.category_id.id != self.uom_id.category_id.id:
                messages.append('La unidad de medida seleccionada debe pertenecer a la misma categoría que la unidad de medida del producto')
                self.uom_id = self.product_id.uom_id.id
            #computar el precio unitario en la UdM de la linea
            self.price_unit = self.product_id.uom_id._compute_price(self.product_id.standard_price, self.uom_id)
            if (company.internal_transfer_steps == '3_step' and requisition.state == 'request') or (company.internal_transfer_steps == '2_step' and requisition.state == 'draft'):
                if company.stock_policy == 'control_stock' or self.env.context.get('force_validation_stock'):
                    messages.extend(self._validate_qty_available(product_qty_validate))
        if messages:
            warning = {'title': _('Información'),
                       'message': "\n".join(messages)
                       }
        return {'domain': domain, 'warning' : warning }


class TransferRequisitionReason(models.Model):

    _name = 'transfer.requisition.reason'
    _description = 'Razones de Diferencia en recepción'
    
    name = fields.Char('Razon')
    product_id = fields.Many2one('product.product', 'Producto')
    line_id = fields.Many2one('transfer.requisition.line', 'Linea de Transferencia')
    requisition_id = fields.Many2one('transfer.requisition', 'Solicitud de transferencia')

