import logging
from datetime import datetime, timedelta

from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class WizardCorrectOrder(models.TransientModel):
    _name = 'wizard.correct.order'
    _description = 'wizard.correct.order'
    
    document_type = fields.Selection([
        ('account','Contabilidad'),
        ('pos','Punto de Venta'),
        ], string='Tipo de Documento', default='pos')
    caf_bad_id = fields.Many2one('dte.caf', 'CAF Erroneo')
    caf_new_id = fields.Many2one('dte.caf', 'CAF Nuevo')
    order_ids = fields.Many2many('pos.order', 'wizard_correct_order_pos_order_rel', 
        'wizard_id', 'order_id', 'Pedidos a modificar')
    invoice_ids = fields.Many2many('account.invoice', 'wizard_correct_order_account_invoice_rel', 
        'wizard_id', 'invoice_id', 'Pedidos a modificar')
    pos_config_id = fields.Many2one('pos.config', 'TPV')
    sii_document_number_start = fields.Integer('Folio de inicio a empezar a corregir', default=lambda self: 0)
    ignore_msj = fields.Boolean('Ignorar Advertencias de No Folio en CAF?')
    is_credit_note = fields.Boolean('Notas de credito?')
    
    @api.onchange('is_credit_note', 'document_type')
    def onchange_is_credit_note(self):
        domain = {}
        if self.is_credit_note:
            domain['caf_bad_id'] = [('sii_document_class','=',61)]
            domain['caf_new_id'] = [('sii_document_class','=',61)]
            if self.document_type == 'pos':
                domain['order_ids'] = [
                    ('sii_document_number','>',0),
                    ('document_class_id.sii_code', '=', 61),
                    ('state','in',('paid', 'done')),
                ]
            else:
                domain['invoice_ids'] = [
                    ('sii_document_number','!=',False),
                    ('document_class_id.sii_code', '=', 61),
                    ('state','in',('open', 'paid')),
                    ('type','=', 'out_refund'),
                ]
        else:
            if self.document_type == 'pos':
                domain['order_ids'] = [
                    ('sii_document_number','>=',0), 
                    ('document_class_id.sii_code', '!=', 61),
                    ('state','in',('draft', 'paid', 'done')),
                ]
            else:
                domain['invoice_ids'] = [
                    ('sii_document_number','!=',False),
                    ('document_class_id.sii_code', '!=', 61), 
                    ('state','in',('open', 'paid')),
                    ('type','=', 'out_invoice'),
                ]
            domain['caf_bad_id'] = []
            domain['caf_new_id'] = []
        return {'domain': domain}
    
    @api.multi
    def get_orders_and_sessions(self):
        sessions = []
        if self.document_type == 'pos':
            pos_model = self.env['pos.order']
            orders = self.order_ids.sorted('id')
            if not orders:
                if self.is_credit_note:
                    orders = pos_model.search([
                        ('sii_document_number','>=',self.sii_document_number_start),
                        ('document_class_id.sii_code', '=', 61),
                    ], order="id")
                else:
                    config = self.pos_config_id
                    if not config:
                        config = self.env['pos.config'].search([('sequence_available_ids','=', self.caf_bad_id.sequence_id.id)])
                    if self.caf_bad_id.sequence_id not in config.sequence_available_ids or self.caf_new_id.sequence_id not in config.sequence_available_ids:
                        raise UserError("El caf seleccionado no pertenece al TPV, por favor verifique")
                    orders = pos_model.search([
                        ('config_id','=',config.id),
                        ('sii_document_number','>=',self.sii_document_number_start),
                        ('sequence_id','=', self.caf_bad_id.sequence_id.id)
                    ], order="id")
            sessions = orders.mapped('session_id').sorted("id")
        else:
            invoice_model = self.env['account.invoice']
            orders = self.invoice_ids.sorted('id')
            if not orders:
                if self.is_credit_note:
                    orders = invoice_model.search([
                        ('sii_document_number','>=',self.sii_document_number_start),
                        ('document_class_id.sii_code', '=', 61),
                        ('state','in',('open', 'paid')),
                        ('type','=', 'out_refund'),
                    ], order="id")
                else:
                    orders = pos_model.search([
                        ('sii_document_number','>=',self.sii_document_number_start),
                        ('document_class_id.sii_code', '!=', 61),
                        ('state','in',('open', 'paid')),
                        ('type','=', 'out_invoice'),
                    ], order="id")
        return orders, sessions
        
    @api.multi
    def _check_folios_remaining(self, orders):
        #validar que desde el inicio, mas el numero de ordenes, no sea mayor al final del caf
        #caso contrario pedir cargar un caf
        check_no_folios = False
        if self.sii_document_number_start > 0 and orders:
            if (self.sii_document_number_start + len(orders)) > self.caf_new_id.final_nm:
                check_no_folios = True
                if not self.ignore_msj:
                    raise UserError("No hay folios disponibles, Inicial: %s, Numero de Ordenes: %s, CAF final calculado: %s. CAF final configurado: %s" % \
                                    (self.sii_document_number_start, len(orders), (self.sii_document_number_start + len(orders)), self.caf_new_id.final_nm))
        return check_no_folios
    
    @api.multi
    def clear_timbre(self, orders):
        if self.document_type == 'pos':
            orders.write({
                'signature': False,
                'sii_batch_number': False,
                'sii_barcode': False,
                'sii_message': False,
                'sii_result': '',
                'canceled': False,
                'sii_send_file_name': '',
            })
            orders.mapped('sii_xml_request').write({
                'sii_xml_response': False,
                'sii_send_ident': False,
            })
        else:
            orders.write({
                'sii_batch_number': False,
                'sii_barcode': False,
                'sii_message': False,
                'sii_result': '',
                'canceled': False,
            })
            orders.mapped('sii_xml_request').write({
                'sii_xml_response': False,
                'sii_send_ident': False,
            })
        return True
    
    @api.multi
    def process_orders(self, orders, check_no_folios):
        total = len(orders)
        count = 0
        _logger.info("Se van a procesar %s ordenes", total)
        start_number = self.caf_new_id.sequence_id.number_next_actual
        set_order_draft = False
        if self.document_type == 'pos':
            for order in orders:
                count += 1
                _logger.info("Procesando %s/%s. Pedido: %s ID: %s", count, total, order.name, order.id)
                if set_order_draft:
                    _logger.info("Pedido: %s ID: %s Se dejo en borrador porque no hay folios disponibles, cargue CAF e intente nuevamente", order.name, order.id)
                    order.state = 'draft'
                    continue
                sii_document_number = self.caf_new_id.sequence_id.next_by_id()
                vals_write = {
                    'sii_document_number': sii_document_number,
                }
                if order.sequence_id != self.caf_new_id.sequence_id:
                    vals_write['sequence_id'] = self.caf_new_id.sequence_id.id
                order.write(vals_write)
                order.sudo(order.create_uid.id).do_validate()
                if order.account_move:
                    order.account_move.sudo().write({
                        'document_class_id': order.document_class_id.id,
                        'sii_document_number': order.sii_document_number,
                        'name': order.sii_document_number,
                    })
                if check_no_folios:
                    #si no hay folios suficients, cuando se terminen, las demas ordenes dejarlas en borrador
                    #para q se procesen despues de cambiar el folio
                    if (int(sii_document_number)+1) > self.caf_new_id.final_nm:
                        set_order_draft = True
        else:
            for order in orders:
                count += 1
                _logger.info("Procesando %s/%s. Pedido: %s ID: %s", count, total, order.sii_document_number, order.id)
                if set_order_draft:
                    _logger.info("Pedido: %s ID: %s No se volvio a timbrar porque no hay folios disponibles, cargue CAF e intente nuevamente", order.sii_document_number, order.id)
#                     order.state = 'draft'
                    continue
                user = order.user_id or self.env.user
                sii_document_number = self.caf_new_id.sequence_id.next_by_id()
                order.sii_document_number = sii_document_number
                order = order.with_context(lang='es_CL')
                order.sii_result = 'NoEnviado'
                order.responsable_envio = user.id
                if order.type in ['out_invoice', 'out_refund']:
                    if order.journal_id.restore_mode:
                        order.sii_result = 'Proceso'
                    else:
                        order._timbrar()
                        prefix = order.journal_document_class_id.sii_document_class_id.doc_code_prefix or ''
                        move_name = (prefix + str(sii_document_number)).replace(' ','')
                        order.write({'move_name': move_name})
                        if order.move_id:
                            document_class_id = order.document_class_id.id
                            guardar = {
                                'document_class_id': document_class_id,
                                'sii_document_number': order.sii_document_number,
                                'no_rec_code':order.no_rec_code,
                                'iva_uso_comun':order.iva_uso_comun,
                                'name': move_name,
                            }
                            order.move_id.write(guardar)
                        if order.picking_ids:
                            order.picking_ids.write({'origin': move_name})
                        pos_order = self.env['pos.order'].search([('invoice_id', '=', order.id), ('document_class_id', '=', order.document_class_id.id)])
                        pos_order.write({'sii_document_number': order.sii_document_number})
                        self.env['sii.cola_envio'].create({
                            'doc_ids':[order.id],
                            'model':'account.invoice',
                            'user_id': user.id,
                            'tipo_trabajo': 'pasivo',
                            'date_time': (datetime.now() + timedelta(hours=12)),
                        })
                if check_no_folios:
                    #si no hay folios suficients, cuando se terminen, las demas ordenes dejarlas en borrador
                    #para q se procesen despues de cambiar el folio
                    if (int(sii_document_number)+1) > self.caf_new_id.final_nm:
                        set_order_draft = True
        return start_number
    
    @api.multi
    def finished_orders(self, sessions, start_number):
        if not self.is_credit_note:
            _logger.info("Verificando sesiones")
            for session in sessions:
                session.action_set_next_document_number()
        return start_number
    
    @api.multi
    def action_process(self):
        orders, sessions = self.get_orders_and_sessions()
        check_no_folios = self._check_folios_remaining(orders)
        if self.sii_document_number_start > 0:
            #configurar en la secuencia el inicio, para q al timbrar, tome desde ese numero
            self.caf_new_id.sequence_id.number_next_actual = self.sii_document_number_start
        _logger.info("Borrando timbraje anterior")
        #borrar los datos de facturacion electronica
        self.clear_timbre(orders)
        start_number = self.process_orders(orders, check_no_folios)
        if self.document_type == 'pos':
            self.finished_orders(sessions, start_number)
        _logger.info("Proceso terminado con exito")
        return True
