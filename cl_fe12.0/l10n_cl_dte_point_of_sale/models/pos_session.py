# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging
import json

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = "pos.session"

    document_available_ids = fields.One2many('pos.session.document.available', 
        'pos_session_id', 'Documentos disponibles a emitir en POS', readonly=True)

    def recursive_xml(self, el):
        if el.text and bool(el.text.strip()):
            return el.text
        res = {}
        for e in el:
            res.setdefault(e.tag, self.recursive_xml(e))
        return res
    
    @api.model
    def _get_next_document_number(self, sequence, raise_exception=True):
        '''
        Calcula el siguiente numero disponible para el tipo de documento solicitado
        @param sequence: Recordset of ir.sequence: tipo de documento solicitado
        @param raise_exception: boolean, Indica si se muestra error en caso de no haber CAF para el documento solicitado
        @return: dict: datos de folios: proximo numero de documento, ultimo numero y el id de la sequencia
        '''
        next_document_number = sequence.number_next
        if sequence.implementation == 'standard':
            next_document_number = sequence.number_next_actual
        try:
            sequence.update_next_by_caf(next_document_number)
        except:
            if raise_exception:
                raise
        new_next_document_number = sequence.number_next
        if sequence.implementation == 'standard':
            new_next_document_number = sequence.number_next_actual
        next_document_number = next_document_number if new_next_document_number == next_document_number else new_next_document_number
        caf_files = sequence.get_caf_files(next_document_number)
        last_document_number = 0
        caf_files_string = ""
        if caf_files:
            last_document_number = caf_files[0].final_nm
            caffs = []
            for caffile in caf_files:
                xml = caffile.decode_caf()
                caffs += [{xml.tag: self.recursive_xml(xml)}]
            if not caffs:
                raise UserError(_("No hay caf disponible para el documento %s folio %s. Por favor suba un CAF o solicite uno en el SII." % 
                                  (sequence.sii_document_class_id.name or sequence.name, next_document_number)))
            caf_files_string = json.dumps(caffs, ensure_ascii=False)
        document_data = {
            'next_document_number': next_document_number,
            'last_document_number': last_document_number,
            'sequence_id': sequence.id,
            'document_class_id': sequence.sii_document_class_id.id,
            'caf_files': caf_files_string,
        }
        return document_data
    
    @api.model
    def _get_documents_availables(self, pos_config):
        '''
        Devolver el listado de documentos que el Punto de venta esta autorizado a emitir
        @param pos_config: pos.config recordset
        @return: Listado de recordset ir.sequence: tipos de docuentos que el punto de impresion puede emitir
        '''
        return pos_config.sequence_available_ids

    @api.multi
    def set_next_document_number(self, raise_exception=True):
        '''
        Calcula y guarda el siguiente numero disponible para cada documento autorizado en el pos
        @param raise_exception: boolean: Mostrar mensaje al usuario cuando no hay CAF vigente
        '''
        self.ensure_one()
        if self.config_id:
            documents_availables = self._get_documents_availables(self.config_id)
            for sequence in documents_availables:
                document_data = self._get_next_document_number(sequence, raise_exception)
                current_document_info = self.document_available_ids.filtered(lambda x: x.sequence_id == sequence)
                if current_document_info:
                    current_document_info.write(document_data)
                else:
                    document_data['pos_session_id'] = self.id
                    self.env['pos.session.document.available'].create(document_data)
        return True
    
    @api.multi
    def action_set_next_document_number(self):
        return self.set_next_document_number()
    
    @api.model
    def create(self, values):
        config_id = values.get('config_id') or self.env.context.get('default_config_id')
        if config_id:
            pos_config = self.env['pos.config'].browse(config_id)
            if pos_config.restore_mode:
                return super(PosSession, self).create(values)
            document_available_list = []
            documents_availables = self._get_documents_availables(pos_config)
            for sequence in documents_availables:
                if not self.env.user.get_digital_signature(sequence.company_id):
                    raise UserError("No Tiene permisos para firmar esta secuencia de folios: %s" % (sequence.name))
                document_data = self._get_next_document_number(sequence)
                document_available_list.append((0, 0, document_data))
            if document_available_list:
                values['document_available_ids'] = document_available_list
        return super(PosSession, self).create(values)

    def _confirm_orders(self):
        # todos los pedidos tipo factura, no crear asiento contable
        # una tarea cron se encargara de facturar los pedidos que aun no tienen factura
        # y el asiento contable se tomara de la factura 
        for session in self:
            company_id = session.config_id.journal_id.company_id.id
            orders = session.order_ids.filtered(lambda order: order.state == 'paid' and order.document_class_id.sii_code not in (33, '33'))
            journal_id = self.env['ir.config_parameter'].sudo().get_param(
                'pos.closing.journal_id_%s' % company_id, default=session.config_id.journal_id.id)
            if not journal_id:
                raise UserError(_("You have to set a Sale Journal for the POS:%s") % (session.config_id.name,))
            ctx = self.env.context.copy()
            ctx.update({'force_company': company_id})
            if orders:
                ctx['move_name'] = orders[0].sii_document_number or orders[0].name
            move = self.env['pos.order'].with_context(ctx)._create_account_move(session.start_at, session.name, int(journal_id), company_id)
            orders.with_context(force_company=company_id)._create_account_move_line(session, move)
            for order in session.order_ids.filtered(lambda o: o.state not in ['done', 'invoiced']):
                if order.state not in ('paid'):
                    raise UserError(
                        _("You cannot confirm all orders of this session, because they have not the 'paid' status.\n"
                          "{reference} is in state {state}, total amount: {total}, paid: {paid}").format(
                            reference=order.pos_reference or order.name,
                            state=order.state,
                            total=order.amount_total,
                            paid=order.amount_paid,
                        ))
                if order.document_class_id.sii_code not in (33, '33'):
                    order.action_pos_order_done()
            orders_to_reconcile = session.order_ids._filtered_for_reconciliation()
            orders_to_reconcile.sudo().with_context(skip_validation_invoice_pos=True)._reconcile_payments()
            orders_to_reconcile.sudo().with_context(skip_validation_invoice_pos=True)._anglo_saxon_reconcile_valuation()
