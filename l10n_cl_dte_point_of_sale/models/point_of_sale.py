# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
import pytz
import logging

_logger = logging.getLogger(__name__)

try:
    from facturacion_electronica import facturacion_electronica as fe
except Exception as e:
    _logger.warning("Problema al cargar Facturación Electrónica %s" % str(e))
try:
    from io import BytesIO
except:
    _logger.warning("no se ha cargado io")
try:
    from suds.client import Client
except:
    pass
try:
    import pdf417gen
except ImportError:
    _logger.info('Cannot import pdf417gen library')
try:
    import base64
except ImportError:
    _logger.info('Cannot import base64 library')

server_url = {'SIICERT': 'https://maullin.sii.cl/DTEWS/','SII':'https://palena.sii.cl/DTEWS/'}

connection_status = {
    '0': 'Upload OK',
    '1': 'El Sender no tiene permiso para enviar',
    '2': 'Error en tamaño del archivo (muy grande o muy chico)',
    '3': 'Archivo cortado (tamaño <> al parámetro size)',
    '5': 'No está autenticado',
    '6': 'Empresa no autorizada a enviar archivos',
    '7': 'Esquema Invalido',
    '8': 'Firma del Documento',
    '9': 'Sistema Bloqueado',
    'Otro': 'Error Interno.',
}


class POSL(models.Model):
    _inherit = 'pos.order.line'

    pos_order_line_id = fields.Integer(
            string="POS Line ID",
            readonly=True,
        )
    
    def _compute_amount_line_all(self):
        self.ensure_one()
        fpos = self.order_id.fiscal_position_id
        tax_ids_after_fiscal_position = fpos.map_tax(self.tax_ids, self.product_id, self.order_id.partner_id) if fpos else self.tax_ids
        price_unit = self.price_unit
        discount = self.discount
        qty = self.qty
        currency_id = self.order_id.pricelist_id.currency_id
        if self.discount_value:
            price_unit = currency_id.round(price_unit * qty) - currency_id.round(self._get_discount_total())
            discount = 0.0
            qty = 1
        taxes = tax_ids_after_fiscal_position.compute_all(price_unit, currency_id, qty, product=self.product_id, partner=self.order_id.partner_id, discount=discount, uom_id=self.product_id.uom_id)
        return {
            'price_subtotal_incl': taxes['total_included'],
            'price_subtotal': taxes['total_excluded'],
        }



class POS(models.Model):
    _inherit = 'pos.order'
    _rec_name = 'sii_document_number' 

    def _get_available_sequence(self):
        ids = [39, 41]
        if self.sequence_id and self.sequence_id.sii_code == 61:
            ids = [61]
        return [('sii_document_class_id.sii_code', 'in', ids)]

    def _get_barcode_img(self):
        for r in self:
            if r.sii_barcode:
                barcodefile = BytesIO()
                image = self.pdf417bc(r.sii_barcode)
                image.save(barcodefile, 'PNG')
                data = barcodefile.getvalue()
                r.sii_barcode_img = base64.b64encode(data)

    signature = fields.Char(
            string="Signature",
        )
    sequence_id = fields.Many2one(
            'ir.sequence',
            string='Sequencia de Boleta',
            states={'draft': [('readonly', False)]},
            domain=lambda self: self._get_available_sequence(),
        )
    document_class_id = fields.Many2one(
            'sii.document_class',
            string='Document Type',
            copy=False,
        )
    sii_code = fields.Integer('Codigo SII', related="document_class_id.sii_code", store=True)
    sii_batch_number = fields.Integer(
            copy=False,
            string='Batch Number',
            readonly=True,
            help='Batch number for processing multiple invoices together',
        )
    sii_barcode = fields.Char(
            copy=False,
            string='SII Barcode',
            readonly=True,
            help='SII Barcode Name',
        )
    sii_barcode_img = fields.Binary(
            copy=False,
            string=_('SII Barcode Image'),
            help='SII Barcode Image in PDF417 format',
            compute='_get_barcode_img',
        )
    sii_xml_request = fields.Many2one(
            'sii.xml.envio',
            string='SII XML Request',
            copy=False,
        )
    sii_result = fields.Selection(
            [
                    ('', 'n/a'),
                    ('NoEnviado', 'No Enviado'),
                    ('EnCola', 'En cola de envío'),
                    ('Enviado', 'Enviado'),
                    ('Aceptado', 'Aceptado'),
                    ('Rechazado', 'Rechazado'),
                    ('Reparo', 'Reparo'),
                    ('Proceso', 'Proceso'),
                    ('Reenviar', 'Reenviar'),
                    ('Anulado', 'Anulado')
            ],
            string='Resultado',
            readonly=True,
            states={'draft': [('readonly', False)]},
            copy=False,
            help="SII request result",
            default='',
        )
    canceled = fields.Boolean(
            string="Canceled?",
        )
    responsable_envio = fields.Many2one(
            'res.users',
        )
    sii_document_number = fields.Integer(
            string="Folio de documento",
            copy=False,
        )
    referencias = fields.One2many(
            'pos.order.referencias',
            'order_id',
            string="References",
            readonly=True,
            states={'draft': [('readonly', False)]},
        )
    sii_xml_dte = fields.Text(
            string='SII XML DTE',
            copy=False,
            readonly=True,
            states={'draft': [('readonly', False)]},
        )
    sii_message = fields.Text(
            string='SII Message',
            copy=False,
        )
    respuesta_ids = fields.Many2many(
            'sii.respuesta.cliente',
            string="Recepción del Cliente",
            readonly=True,
        )
    timestamp_timbre = fields.Char(
        string="TimeStamp Timbre"
    )
    mig_res_id = fields.Integer(u'ID Importado', index=True)
    
    @api.onchange('statement_ids', 'lines')
    def _onchange_amount_all(self):
        for order in self.with_context(round=False):
            currency = order.pricelist_id.currency_id
            order.amount_paid = sum(payment.amount for payment in order.statement_ids)
            order.amount_return = sum(payment.amount < 0 and payment.amount or 0 for payment in order.statement_ids)
            order.amount_tax = currency.round(sum(self._amount_line_tax(line, order.fiscal_position_id) for line in order.lines))
            amount_untaxed = currency.round(sum(line._compute_amount_line_all()['price_subtotal'] for line in order.lines))
            order.amount_total = order.amount_tax + amount_untaxed

    @api.model
    def _amount_line_tax(self, line, fiscal_position_id):
        taxes = line.tax_ids.filtered(lambda t: t.company_id.id == line.order_id.company_id.id)
        if fiscal_position_id:
            taxes = fiscal_position_id.map_tax(taxes, line.product_id, line.order_id.partner_id)
        cur = line.order_id.pricelist_id.currency_id
        price_unit = line.price_unit
        discount = line.discount
        qty = line.qty
        if line.discount_value:
            price_unit = cur.round(price_unit * qty) - cur.round(line._get_discount_total())
            discount = 0.0
            qty = 1
        taxes = taxes.compute_all(price_unit, cur, qty, product=line.product_id, partner=line.order_id.partner_id or False, discount=discount, uom_id=line.product_id.uom_id)['taxes']
        return sum(tax.get('amount', 0.0) for tax in taxes)

    def crear_intercambio(self):
        envio = self._crear_envio(RUTRecep=self.partner_id.rut())
        result = fe.xml_envio(envio)
        return result['sii_xml_request'].encode('ISO-8859-1')

    def _create_attachment(self,):
        url_path = '/download/xml/boleta/%s' % (self.id)
        filename = ('%s%s.xml' % (self.document_class_id.doc_code_prefix, self.sii_document_number)).replace(' ', '_')
        att = self.env['ir.attachment'].search(
                [
                    ('name', '=', filename),
                    ('res_id', '=', self.id),
                    ('res_model', '=', 'pos.order')
                ],
                limit=1,
            )
        if att:
            return att
        xml_intercambio = self.crear_intercambio()
        data = base64.b64encode(xml_intercambio)
        values = dict(
                        name=filename,
                        datas_fname=filename,
                        url=url_path,
                        res_model='pos.order',
                        res_id=self.id,
                        type='binary',
                        datas=data,
                    )
        att = self.env['ir.attachment'].sudo().create(values)
        return att

    @api.multi
    def get_xml_file(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/download/xml/boleta/%s' % (self.id),
            'target': 'self',
        }

    def get_folio(self):
        return int(self.sii_document_number)

    def pdf417bc(self, ted):
        bc = pdf417gen.encode(
            ted,
            security_level=5,
            columns=13,
            encoding='ISO-8859-1',
        )
        image = pdf417gen.render_image(
            bc,
            padding=15,
            scale=1,
        )
        return image

    def _acortar_str(self, texto, size=1):
        c = 0
        cadena = ""
        while c < size and c < len(texto):
            cadena += texto[c]
            c += 1
        return cadena
    
    @api.model
    def _order_fields(self, ui_order):
        vals = super(POS, self)._order_fields(ui_order)
        if ui_order.get('sii_document_number'):
            vals['sii_document_number'] = ui_order.get('sii_document_number')
        if ui_order.get('sequence_id'):
            sequence = self.env['ir.sequence'].browse(ui_order.get('sequence_id'))
            vals['sequence_id'] = ui_order.get('sequence_id')
            vals['document_class_id'] = sequence.sii_document_class_id.id
            if not vals.get('partner_id') and ui_order.get('statement_ids'):
                if sequence.sii_document_class_id.sii_code not in (33, 61):
                    partner = self.env.ref('l10n_cl_fe.par_cfa', False)
                    if partner:
                        vals['partner_id'] = partner.id
        if ui_order.get('signature'):
            vals['signature'] = ui_order.get('signature')
        if ui_order.get('sequence_number'): #FIX odoo bug
            vals['sequence_number'] = ui_order.get('sequence_number')
        return vals

    @api.model
    def _process_order(self, order):
        lines = []
        for l in order['lines']:
            l[2]['pos_order_line_id'] = int(l[2]['id'])
            lines.append(l)
        order['lines'] = lines
        order_id = super(POS, self)._process_order(order)
        if order_id.amount_total != float(order['amount_total']):
            raise UserError("Diferencia de cálculo, verificar. En el caso de que el cálculo use Mepco, debe intentar cerrar la caja porque el valor a cambiado")
        return order_id

    def _prepare_invoice(self):
        result = super(POS, self)._prepare_invoice()
        sale_journal = self.session_id.config_id.invoice_journal_id
        journal_document_class_id = self.env['account.journal.sii_document_class'].search([
            ('journal_id', '=', sale_journal.id),
            ('sii_document_class_id.sii_code', 'in', [33]),
            ('sequence_id', '=', self.sequence_id.id),
            ], limit=1)
        if not journal_document_class_id:
            raise UserError("Por favor defina Secuencia de Facturas para el Journal %s" % sale_journal.name)
        result.update({
            'activity_description': self.partner_id.activity_description.id,
            'ticket':  self.session_id.config_id.ticket,
            'journal_document_class_id': journal_document_class_id.id,
            'document_class_ids': journal_document_class_id.sii_document_class_id.id,
            'responsable_envio': self.env.uid,
            'date_invoice': fields.Date.context_today(self, self.date_order),
        })
        if self.sii_document_number:
            result['sii_document_number'] = self.sii_document_number
            result['move_name'] = self.sii_document_number
        if self.session_id.config_id.crm_team_id:
            result['team_id'] = self.session_id.config_id.crm_team_id.id
        if self.session_id.config_id.warehouse_id:
            result['warehouse_id'] = self.session_id.config_id.warehouse_id.id
        return result

    @api.multi
    def do_validate(self):
        ids = []
        force_timbre = self.env.context.get('force_timbre')
        for order in self:
            if order.session_id.config_id.restore_mode:
                continue
            if order.document_class_id.sii_code in [35]:
                continue
            if not order.session_id.config_id.timbrar_online and not force_timbre and order.document_class_id.es_boleta():
                continue
            order._timbrar()
            if order.document_class_id.sii_code in [61]:
                ids.append(order.id)
        if ids:
            order.sii_result = 'EnCola'
            tiempo_pasivo = (datetime.now() + timedelta(hours=int(self.env['ir.config_parameter'].sudo().get_param('account.auto_send_dte', default=12))))
            self.env['sii.cola_envio'].sudo().create({
                'company_id': self[0].company_id.id,
                'doc_ids': ids,
                'model': 'pos.order',
                'user_id': self.env.uid,
                'tipo_trabajo': 'pasivo',
                'date_time': tiempo_pasivo,
                'send_email': False if self[0].company_id.dte_service_provider=='SIICERT' or not self.env['ir.config_parameter'].sudo().get_param('account.auto_send_email', default=True) else True,
            })

    @api.multi
    def do_dte_send_order(self):
        ids = []
        for order in self:
            if not order.invoice_id and order.document_class_id.sii_code in [61, 39, 41]:
                if order.sii_result not in [False, '', 'NoEnviado', 'Rechazado']:
                    raise UserError("El documento %s ya ha sido enviado o está en cola de envío" % order.sii_document_number)
                ids.append(order.id)
        if ids:
            self.env['sii.cola_envio'].sudo().create({
                'company_id': self[0].company_id.id,
                'doc_ids': ids,
                'model': 'pos.order',
                'user_id': self.env.uid,
                'tipo_trabajo': 'envio',
                'send_email': False if self[0].company_id.dte_service_provider=='SIICERT' or not self.env['ir.config_parameter'].sudo().get_param('account.auto_send_email', default=True) else True,
            })

    def _giros_emisor(self):
        giros_emisor = []
        i=0
        for turn in self.company_id.company_activities_ids:
            if i < 4:
                giros_emisor.append(turn.code)
            i += 1
        return giros_emisor

    def _id_doc(self, taxInclude=False, MntExe=0):
        util_model = self.env['odoo.utils']
        from_zone = pytz.UTC
        to_zone = pytz.timezone('America/Santiago')
        date_order = util_model._change_time_zone(self.date_order, from_zone, to_zone)
        IdDoc = {}
        IdDoc['TipoDTE'] = self.document_class_id.sii_code
        IdDoc['Folio'] = self.get_folio()
        IdDoc['FchEmis'] = date_order.strftime(DF)
        if self.document_class_id.es_boleta():
            IdDoc['IndServicio'] = 3 #@TODO agregar las otras opciones a la fichade producto servicio
        else:
            IdDoc['TpoImpresion'] = "T"
            IdDoc['MntBruto'] = 1
            IdDoc['FmaPago'] = 1
        #if self.tipo_servicio:
        #    Encabezado['IdDoc']['IndServicio'] = 1,2,3,4
        # todo: forma de pago y fecha de vencimiento - opcional
        if not taxInclude and self.document_class_id.es_boleta():
            IdDoc['IndMntNeto'] = 2
        #if self.document_class_id.es_boleta():
            #Servicios periódicos
        #    IdDoc['PeriodoDesde'] =
        #    IdDoc['PeriodoHasta'] =
        return IdDoc

    def _emisor(self):
        Emisor = {}
        Emisor['RUTEmisor'] = self.company_id.partner_id.rut()
        if self.document_class_id.es_boleta():
            Emisor['RznSocEmisor'] = self.company_id.partner_id.name
            Emisor['GiroEmisor'] = self._acortar_str(self.company_id.activity_description.name, 80)
        else:
            Emisor['RznSoc'] = self.company_id.partner_id.name
            Emisor['GiroEmis'] = self._acortar_str(self.company_id.activity_description.name, 80)
            Emisor['Telefono'] = self.company_id.phone or ''
            Emisor['CorreoEmisor'] = self.company_id.dte_email_id.name_get()[0][1]
            Emisor['Actecos'] = self._giros_emisor()
        if self.sale_journal.sucursal_id:
            Emisor['Sucursal'] = self.sale_journal.sucursal_id.name
            Emisor['CdgSIISucur'] = self.sale_journal.sucursal_id.sii_code
        Emisor['DirOrigen'] = self.company_id.street + ' ' +(self.company_id.street2 or '')
        Emisor['CmnaOrigen'] = self.company_id.city_id.name or ''
        Emisor['CiudadOrigen'] = self.company_id.city or ''
        Emisor["Modo"] = "produccion" if self.company_id.dte_service_provider == 'SII'\
                  else 'certificacion'
        Emisor["NroResol"] = self.company_id.dte_resolution_number
        Emisor["FchResol"] = self.company_id.dte_resolution_date.strftime('%Y-%m-%d')
        Emisor["ValorIva"] = 19
        return Emisor

    def _receptor(self):
        Receptor = {}
        #Receptor['CdgIntRecep']
        Receptor['RUTRecep'] = self.partner_id.rut()
        Receptor['RznSocRecep'] = self._acortar_str(self.partner_id.name or "Usuario Anonimo", 100)
        if self.partner_id.phone:
            Receptor['Contacto'] = self.partner_id.phone
        if self.partner_id.dte_email and not self.document_class_id.es_boleta():
            Receptor['CorreoRecep'] = self.partner_id.dte_email
        if self.partner_id.street:
            Receptor['DirRecep'] = self.partner_id.street+ ' ' + (self.partner_id.street2 or '')
        if self.partner_id.city_id:
            Receptor['CmnaRecep'] = self.partner_id.city_id.name
        if self.partner_id.city:
            Receptor['CiudadRecep'] = self.partner_id.city
        return Receptor

    def _totales(self, MntExe=0, no_product=False, taxInclude=False):
        currency = self.pricelist_id.currency_id
        Totales = {}
        amount_total = currency.round(self.amount_total)
        if amount_total < 0:
            amount_total *= -1
        if no_product:
            amount_total = 0
        else:
            if self.document_class_id.sii_code in [34, 41] and self.amount_tax > 0:
                raise UserError("NO pueden ir productos afectos en documentos exentos")
            amount_untaxed = self.amount_total - self.amount_tax
            if amount_untaxed < 0:
                amount_untaxed *= -1
            if MntExe < 0:
                MntExe *= -1
            if self.amount_tax == 0 and MntExe > 0 and self.document_class_id.sii_code in [39]:
                raise UserError("Debe ir almenos un Producto Afecto")
            Neto = amount_untaxed - MntExe
            IVA = False
            if Neto > 0 and (not self.document_class_id.es_boleta() or self._context.get('tax_detail')):
                for l in self.lines:
                    for t in l.tax_ids:
                        if t.sii_code in [14, 15]:
                            IVA = True
                            IVAAmount = round(t.amount,2)
                if IVA:
                    Totales['MntNeto'] = currency.round(Neto)
            if MntExe > 0:
                Totales['MntExe'] = currency.round(MntExe)
            if IVA and not self.document_class_id.es_boleta() or self._context.get('tax_detail'):
                Totales['TasaIVA'] = IVAAmount
                iva = currency.round(self.amount_tax)
                if iva < 0:
                    iva *= -1
                Totales['IVA'] = iva
            #if IVA and IVA.tax_id.sii_code in [15]:
            #    Totales['ImptoReten'] = collections.OrderedDict()
            #    Totales['ImptoReten']['TpoImp'] = IVA.tax_id.sii_code
            #    Totales['ImptoReten']['TasaImp'] = round(IVA.tax_id.amount,2)
            #    Totales['ImptoReten']['MontoImp'] = int(round(IVA.amount))
        Totales['MntTotal'] = amount_total

        #Totales['MontoNF']
        #Totales['TotalPeriodo']
        #Totales['SaldoAnterior']
        #Totales['VlrPagar']
        return Totales

    def _encabezado(self, MntExe=0, no_product=False, taxInclude=False):
        Encabezado = {}
        Encabezado['IdDoc'] = self._id_doc(taxInclude, MntExe)
        Encabezado['Emisor'] = self._emisor()
        Encabezado['Receptor'] = self._receptor()
        Encabezado['Totales'] = self._totales(MntExe, no_product, taxInclude)
        return Encabezado

    def _invoice_lines(self):
        currency = self.pricelist_id.currency_id
        line_number = 1
        invoice_lines = []
        no_product = False
        MntExe = 0
        for line in self.with_context(lang="es_CL").lines:
            if line.product_id.default_code == 'NO_PRODUCT':
                no_product = True
            lines = {}
            lines['NroLinDet'] = line_number
            if line.product_id.default_code and not no_product:
                lines['CdgItem'] = {}
                lines['CdgItem']['TpoCodigo'] = 'INT1'
                lines['CdgItem']['VlrCodigo'] = line.product_id.default_code
            taxInclude = False
            for t in line.tax_ids:
                taxInclude = t.price_include
                if t.amount == 0 or t.sii_code in [0]:#@TODO mejor manera de identificar exento de afecto
                    lines['IndExe'] = 1
                    MntExe += int(round(line.price_subtotal_incl, 0))
            #if line.product_id.type == 'events':
            #   lines['ItemEspectaculo'] =
#            if self.document_class_id.es_boleta():
#                lines['RUTMandante']
            lines['NmbItem'] = self._acortar_str(line.product_id.name,80) #
            lines['DscItem'] = self._acortar_str(line.name, 1000) #descripción más extenza
            if line.product_id.default_code:
                lines['NmbItem'] = self._acortar_str(line.product_id.name.replace('['+line.product_id.default_code+'] ',''),80)
            #lines['InfoTicket']
            qty = round(line.qty, 4)
            if qty < 0:
                qty *= -1
            if not no_product:
                lines['QtyItem'] = qty
            if qty == 0 and not no_product:
                lines['QtyItem'] = 1
                #raise UserError("NO puede ser menor que 0")
            if not no_product:
                lines['UnmdItem'] = line.product_id.uom_id.name[:4]
                lines['PrcItem'] = round(abs(line.price_unit), 4)
            if not no_product and not taxInclude:
                price = int(round(line.price_subtotal, 0))
            elif not no_product:
                price = int(round(line.price_subtotal_incl, 0))
            if price < 0:
                price *= -1
            # el descuento pasarlo en monto, no en porcentaje
            if line.discount_value > 0:
                lines['DescuentoMonto'] = int(round(line.discount_value * qty))
            elif line.discount > 0:
                lines['DescuentoMonto'] = int(round((((line.discount / 100) * lines['PrcItem']) * qty)))
            lines['MontoItem'] = price
            if no_product:
                lines['MontoItem'] = 0
            line_number += 1
            if lines.get('PrcItem', 1) == 0:
                del(lines['PrcItem'])
            invoice_lines.append(lines)
        return {
                'Detalle': invoice_lines,
                'MntExe': MntExe,
                'no_product': no_product,
                'tax_include': taxInclude,
                }

    def _valida_referencia(self, ref):
        if ref.origen in [False, '', 0]:
            raise UserError("Debe incluir Folio de Referencia válido")

    def _dte(self, is_for_libro=False):
        dte = {}
        invoice_lines = self._invoice_lines()
        dte['Encabezado'] = self._encabezado(
            invoice_lines['MntExe'],
            invoice_lines['no_product'],
            invoice_lines['tax_include'],
        )
        lin_ref = 1
        ref_lines = []
        if self.company_id.dte_service_provider == 'SIICERT' and self.document_class_id.es_boleta():
            RazonRef = "CASO-" + str(self.sii_batch_number)
            ref_line = {}
            ref_line['NroLinRef'] = lin_ref
            ref_line['CodRef'] = "SET"
            ref_line['RazonRef'] = RazonRef
            lin_ref = 2
            ref_lines.append(ref_line)
        for ref in self.referencias:
            ref_line = {}
            ref_line['NroLinRef'] = lin_ref
            self._valida_referencia(ref)
            if not self.document_class_id.es_boleta():
                if ref.sii_referencia_TpoDocRef:
                    ref_line['TpoDocRef'] = ref.sii_referencia_TpoDocRef.sii_code
                    ref_line['FolioRef'] = ref.origen
                ref_line['FchRef'] = ref.fecha_documento or fields.Date.context_today(self).strftime(DF)
            if ref.sii_referencia_CodRef not in ['', 'none', False]:
                ref_line['CodRef'] = ref.sii_referencia_CodRef
            ref_line['RazonRef'] = ref.motivo
            if self.document_class_id.es_boleta():
                ref_line['CodVndor'] = self.user_id.id
                ref_line['CodCaja'] = self.location_id.name
            ref_lines.append(ref_line)
            lin_ref += 1
        dte['Detalle'] = invoice_lines['Detalle']
        dte['Referencia'] = ref_lines
        return dte

    def _get_datos_empresa(self, company_id):
        signature_id = self.env.user.get_digital_signature(company_id)
        if not signature_id:
            raise UserError(_('''There are not a Signature Cert Available for this user, please upload your signature or tell to someelse.'''))
        emisor = self._emisor()
        return {
            "Emisor": emisor,
            "firma_electronica": signature_id.parametros_firma(),
        }

    def _timbrar(self):
        folio = self.get_folio()
        doc_id_number = "F{}T{}".format(folio, self.document_class_id.sii_code)
        doc_id = '<Documento ID="{}">'.format(doc_id_number)
        dte = self._get_datos_empresa(self.company_id)
        dte['Documento'] = [{
            'TipoDTE': self.document_class_id.sii_code,
            'caf_file': [self.sequence_id.get_caf_file(
                            folio, decoded=False).decode()],
            'documentos': [self._dte()]
            },
        ]
        result = fe.timbrar(dte)
        if result[0].get('error'):
            raise UserError(result[0].get('error'))
        self.write({
            'sii_xml_dte': result[0]['sii_xml_request'],
            'sii_barcode': result[0]['sii_barcode'],
        })
        return

    def _crear_envio(self, RUTRecep="60803000-K"):
        grupos = {}
        batch = 0
        for r in self.with_context(lang='es_CL'):
            batch += 1
            if r.sii_result in ['Rechazado'] or r.company_id.dte_service_provider == 'SIICERT':
                r._timbrar()
            #@TODO Mejarorar esto en lo posible
            grupos.setdefault(r.document_class_id.sii_code, [])
            grupos[r.document_class_id.sii_code].append({
                'NroDTE': r.sii_batch_number,
                'sii_xml_request': r.sii_xml_dte,
                'Folio': r.get_folio(),
            })
        envio = self[0]._get_datos_empresa(self[0].company_id)
        envio.update({
            'RutReceptor': RUTRecep,
            'Documento': []
        })
        for k, v in grupos.items():
            envio['Documento'].append(
                {
                    'TipoDTE': k,
                    'documentos': v,
                }
            )
        return envio

    @api.multi
    def do_dte_send(self, n_atencion=None):
        datos = self._crear_envio()
        result = fe.timbrar_y_enviar(datos)
        envio_id = self[0].sii_xml_request
        envio = {
                'xml_envio': result['sii_xml_request'],
                'name': result['sii_send_filename'],
                'company_id': self[0].company_id.id,
                'user_id': self.env.uid,
                'sii_send_ident': result.get('sii_send_ident'),
                'sii_xml_response': result.get('sii_xml_response'),
                'state': result.get('sii_result'),
            }
        if self[0].document_class_id.es_boleta() and self[0].company_id.dte_service_provider == 'SII':
            envio.update({
                'state': "Aceptado",
                'sii_send_ident': 'BE'
            })
        if not envio_id:
            envio_id = self.env['sii.xml.envio'].create(envio)
            for i in self:
                i.sii_xml_request = envio_id.id
                i.sii_result = 'Enviado'
        else:
            envio_id.write(envio)
        return envio_id

    @api.onchange('sii_message')
    def get_sii_result(self):
        for r in self:
            if r.company_id.dte_service_provider != 'SIICERT' and r.document_class_id.es_boleta():
                r.sii_result = 'Proceso'
                continue
            if r.sii_message:
                r.sii_result = self.env['account.invoice'].process_response_xml(r.sii_message)
                continue
            if r.sii_xml_request.state == 'NoEnviado':
                r.sii_result = 'EnCola'
                continue
            r.sii_result = r.sii_xml_request.state

    def _get_dte_status(self):
        for r in self:
            if r.sii_xml_request and r.sii_xml_request.state not in ['Aceptado', 'Rechazado']:
                continue
            token = r.sii_xml_request.get_token(self.env.user, r.company_id)
            url = server_url[r.company_id.dte_service_provider] + 'QueryEstDte.jws?WSDL'
            _server = Client(url)
            receptor = r.partner_id.rut()
            util_model = self.env['odoo.utils']
            from_zone = pytz.UTC
            to_zone = pytz.timezone('America/Santiago')
            date_order = util_model._change_time_zone(r.date_order, from_zone, to_zone).strftime("%d-%m-%Y")
            signature_id = self.env.user.get_digital_signature(r.company_id)
            rut = signature_id.subject_serial_number
            amount_total = r.amount_total if r.amount_total >= 0 else r.amount_total*-1
            try:
                respuesta = _server.service.getEstDte(
                    rut[:-2],
                    str(rut[-1]),
                    r.company_id.partner_id.rut()[:-2],
                    r.company_id.partner_id.rut()[-1],
                    receptor[:-2],
                    receptor[-1],
                    str(r.document_class_id.sii_code),
                    str(r.sii_document_number),
                    date_order,
                    str(int(amount_total)),
                    token,
                )
                r.sii_message = respuesta
            except Exception as e:
                msg = "Error al obtener Estado DTE"
                _logger.warning("%s: %s" % (msg, str(e)))
                if e.args[0][0] == 503:
                    raise UserError('%s: Conexión al SII caída/rechazada o el SII está temporalmente fuera de línea, reintente la acción' % (msg))
                raise UserError(("%s: %s" % (msg, str(e))))

    @api.multi
    def ask_for_dte_status(self):
        for r in self:
            if r.document_class_id.es_boleta() and r.company_id.dte_service_provider != 'SIICERT':
                continue
            if not r.sii_xml_request and not r.sii_xml_request.sii_send_ident:
                raise UserError('No se ha enviado aún el documento, aún está en cola de envío interna en odoo')
            if r.sii_xml_request.state not in ['Aceptado', 'Rechazado']:
                r.sii_xml_request.get_send_status(r.env.user)
        try:
            self._get_dte_status()
        except Exception as e:
            _logger.warning("Error al obtener DTE Status: %s" %str(e))
        self.get_sii_result()

    def send_exchange(self):
        att = self._create_attachment()
        body = 'XML de Intercambio DTE: %s%s' % (self.document_class_id.doc_code_prefix, self.sii_document_number)
        subject = 'XML de Intercambio DTE: %s%s' % (self.document_class_id.doc_code_prefix, self.sii_document_number)
        dte_email_id = self.company_id.dte_email_id or self.env.user.company_id.dte_email_id
        dte_receptors = self.partner_id.commercial_partner_id.child_ids + self.partner_id.commercial_partner_id
        email_to = ''
        for dte_email in dte_receptors:
            if not dte_email.send_dte:
                continue
            email_to += dte_email.name+','
        values = {
                'res_id': self.id,
                'email_from': dte_email_id.name_get()[0][1],
                'email_to': email_to[:-1],
                'auto_delete': False,
                'model': 'pos.order',
                'body': body,
                'subject': subject,
                'attachment_ids': [[6, 0, att.ids]],
            }
        send_mail = self.env['mail.mail'].sudo().create(values)
        send_mail.send()

    def _create_account_move(self, dt, ref, journal_id, company_id):
        date_tz_user = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(dt))
        date_tz_user = fields.Date.to_string(date_tz_user)
        move_vals = {'ref': ref, 'journal_id': journal_id, 'date': date_tz_user}
        if self.env.context.get('move_name'):
            move_vals['name'] = self.env.context.get('move_name')
        return self.env['account.move'].sudo().create(move_vals)

    def _prepare_account_move_and_lines(self, session=None, move=None):
        def _flatten_tax_and_children(taxes, group_done=None):
            children = self.env['account.tax']
            if group_done is None:
                group_done = set()
            for tax in taxes.filtered(lambda t: t.amount_type == 'group'):
                if tax.id not in group_done:
                    group_done.add(tax.id)
                    children |= _flatten_tax_and_children(tax.children_tax_ids, group_done)
            return taxes + children

        # Tricky, via the workflow, we only have one id in the ids variable
        """Create a account move line of order grouped by products or not."""
        IrProperty = self.env['ir.property']
        ResPartner = self.env['res.partner']

        if session and not all(session.id == order.session_id.id for order in self):
            raise UserError(_('Selected orders do not have the same session!'))

        grouped_data = {}
        have_to_group_by = session and session.config_id.group_by or False
        rounding_method = session and session.config_id.company_id.tax_calculation_rounding_method

        def add_anglosaxon_lines(grouped_data, date_order, company_id):
            Product = self.env['product.product']
            Analytic = self.env['account.analytic.account']
            for product_key in list(grouped_data.keys()):
                if product_key[0] == "product":
                    for line in grouped_data[product_key]:
                        product = Product.browse(line['product_id']).with_context(history_date=date_order, force_company=company_id)
                        # In the SO part, the entries will be inverted by function compute_invoice_totals
                        price_unit = self._get_pos_anglo_saxon_price_unit(product, line['partner_id'], line['quantity'])
                        account_analytic = Analytic.browse(line.get('analytic_account_id'))
                        res = Product._anglo_saxon_sale_move_lines(
                            line['name'], product, product.uom_id, line['quantity'], price_unit,
                                fiscal_position=order.fiscal_position_id,
                                account_analytic=account_analytic)
                        if res:
                            line1, line2 = res
                            line1['tax_ids'] = [(6, 0, [])]
                            line2['tax_ids'] = [(6, 0, [])]
                            line1 = Product._convert_prepared_anglosaxon_line(line1, order.partner_id)
                            insert_data('product', line1)
    
                            line2 = Product._convert_prepared_anglosaxon_line(line2, order.partner_id)
                            insert_data('product', line2)

        total_debit, total_credit, line_index = 0.0, 0.0, 0
        last_line, last_line_data = False, False
        for order in self.filtered(lambda o: not o.account_move or o.state == 'paid'):
            total_debit, total_credit, line_index = 0.0, 0.0, 0
            last_line, last_line_data = False, False
            current_company = order.sale_journal.company_id
            account_def = IrProperty.get(
                'property_account_receivable_id', 'res.partner')
            order_account = order.partner_id.property_account_receivable_id.id or account_def and account_def.id
            partner_id = ResPartner._find_accounting_partner(order.partner_id).id or False
            if move is None:
                # Create an entry for the sale
                journal_id = self.env['ir.config_parameter'].sudo().get_param(
                    'pos.closing.journal_id_%s' % current_company.id, default=order.sale_journal.id)
                move = self.with_context(move_name=order.sii_document_number or order.name)._create_account_move(
                    order.session_id.start_at, order.name, int(journal_id), order.company_id.id)

            def insert_data(data_type, values):
                # if have_to_group_by:
                values.update({
                    'partner_id': partner_id,
                    'move_id': move.id,
                })

                key = self._get_account_move_line_group_data_type_key(data_type, values, {'rounding_method': rounding_method})
                if not key:
                    return

                grouped_data.setdefault(key, [])

                if have_to_group_by:
                    if not grouped_data[key]:
                        grouped_data[key].append(values)
                    else:
                        current_value = grouped_data[key][0]
                        current_value['quantity'] = current_value.get('quantity', 0.0) + values.get('quantity', 0.0)
                        current_value['credit'] = current_value.get('credit', 0.0) + values.get('credit', 0.0)
                        current_value['debit'] = current_value.get('debit', 0.0) + values.get('debit', 0.0)
                        if 'currency_id' in values:
                            current_value['amount_currency'] = current_value.get('amount_currency', 0.0) + values.get('amount_currency', 0.0)
                        if key[0] == 'tax' and rounding_method == 'round_globally':
                            if current_value['debit'] - current_value['credit'] > 0:
                                current_value['debit'] = current_value['debit'] - current_value['credit']
                                current_value['credit'] = 0
                            else:
                                current_value['credit'] = current_value['credit'] - current_value['debit']
                                current_value['debit'] = 0

                else:
                    grouped_data[key].append(values)

            # because of the weird way the pos order is written, we need to make sure there is at least one line,
            # because just after the 'for' loop there are references to 'line' and 'income_account' variables (that
            # are set inside the for loop)
            # TOFIX: a deep refactoring of this method (and class!) is needed
            # in order to get rid of this stupid hack
            assert order.lines, _('The POS order must have lines when calling this method')
            # Create an move for each order line
            cur = order.pricelist_id.currency_id
            cur_company = order.company_id.currency_id
            amount_cur_company = 0.0
            date_order = order.date_order.date() if order.date_order else fields.Date.today()
            move_lines = []
            order_lines = order.lines.sorted('price_subtotal')
            for line in order_lines:
                line_index += 1
                last_line = line_index == len(order.lines)
                if cur != cur_company:
                    amount_subtotal = cur._convert(line.price_subtotal, cur_company, order.company_id, date_order)
                else:
                    amount_subtotal = line.price_subtotal

                # Search for the income account
                if line.product_id.property_account_income_id.id:
                    income_account = line.product_id.property_account_income_id.id
                elif line.product_id.categ_id.property_account_income_categ_id.id:
                    income_account = line.product_id.categ_id.property_account_income_categ_id.id
                else:
                    raise UserError(_('Please define income '
                                      'account for this product: "%s" (id:%d).')
                                    % (line.product_id.name, line.product_id.id))

                name = line.product_id.name
                if line.notice:
                    # add discount reason in move
                    name = name + ' (' + line.notice + ')'

                # Create a move for the line for the order line
                # Just like for invoices, a group of taxes must be present on this base line
                # As well as its children
                base_line_tax_ids = _flatten_tax_and_children(line.tax_ids_after_fiscal_position).filtered(lambda tax: tax.type_tax_use in ['sale', 'none'])
                data = {
                    'name': name,
                    'quantity': line.qty,
                    'product_id': line.product_id.id,
                    'account_id': income_account,
                    'analytic_account_id': self._prepare_analytic_account(line),
                    'credit': ((amount_subtotal > 0) and amount_subtotal) or 0.0,
                    'debit': ((amount_subtotal < 0) and -amount_subtotal) or 0.0,
                    'tax_ids': [(6, 0, base_line_tax_ids.ids)],
                    'partner_id': partner_id
                }
                if cur != cur_company:
                    data['currency_id'] = cur.id
                    data['amount_currency'] = -abs(line.price_subtotal) if data.get('credit') else abs(line.price_subtotal)
                    amount_cur_company += data['credit'] - data['debit']
                if not last_line:
                    insert_data('product', data)
                    move_lines.append({'data_type': 'product', 'values': data})
                else:
                    last_line_data = data.copy()
                total_credit += data['credit']
                total_debit += data['debit']

            # Create the tax lines
            for tax in order.tax_ids:
                if cur != cur_company:
                    round_tax = False if rounding_method == 'round_globally' else True
                    amount_tax = cur._convert(tax['amount'], cur_company, order.company_id, date_order, round=round_tax)
                else:
                    amount_tax = tax.amount
                data = {
                    'name': tax.tax_id.name,
                    'account_id': tax.tax_id.account_id.id or income_account,
                    'credit': ((amount_tax > 0) and amount_tax) or 0.0,
                    'debit': ((amount_tax < 0) and -amount_tax) or 0.0,
                    'tax_line_id': tax.tax_id.id,
                    'partner_id': partner_id,
                    'order_id': order.id
                }
                if cur != cur_company:
                    data['currency_id'] = cur.id
                    data['amount_currency'] = -abs(tax.amount) if data.get('credit') else abs(tax.amount)
                    amount_cur_company += data['credit'] - data['debit']
                insert_data('tax', data)
                move_lines.append({'data_type': 'tax', 'values': data})
                total_credit += data['credit']
                total_debit += data['debit']

            # round tax lines per order
            if rounding_method == 'round_globally':
                for group_key, group_value in grouped_data.items():
                    if group_key[0] == 'tax':
                        for line in group_value:
                            line['credit'] = cur_company.round(line['credit'])
                            line['debit'] = cur_company.round(line['debit'])
                            if line.get('currency_id'):
                                line['amount_currency'] = cur.round(line.get('amount_currency', 0.0))

            receivable_amounts = order._get_amount_receivable(move_lines)

            data = {
                'name': _("Trade Receivables"),  # order.name,
                'account_id': order_account,
                'credit': ((receivable_amounts['amount'] < 0) and -receivable_amounts['amount']) or 0.0,
                'debit': ((receivable_amounts['amount'] > 0) and receivable_amounts['amount']) or 0.0,
                'partner_id': partner_id
            }
            if receivable_amounts['amount_currency']:
                data['currency_id'] = cur.id
                data['amount_currency'] = -abs(receivable_amounts['amount_currency']) if data.get('credit') else abs(receivable_amounts['amount_currency'])
            insert_data('counter_part', data)
            total_credit += data['credit']
            total_debit += data['debit']
            dif = total_debit - total_credit
            if last_line_data:
                if not cur.is_zero(dif):
                    _logger.info(u"Creando ajuste en Pedido: %s ID: %s, producto: %s", order.sii_document_number, order.id, last_line_data['name'])
                    #debito > credito
                    #si hay credito, sumarlo al credito para igualar
                    #si hay debito, restarlo para igualar
                    if dif > 0:
                        if last_line_data['credit'] > 0:
                            last_line_data['credit'] += dif
                        else:
                            last_line_data['debit'] -= dif
                    #debito < credito
                    #si hay credito, sumarlo al credito para igualar
                    #si hay debito, restarlo para igualar
                    else:
                        if last_line_data['credit'] > 0:
                            last_line_data['credit'] -= abs(dif)
                        else:
                            last_line_data['debit'] += abs(dif)
                    last_line_data['name'] = "*" + last_line_data['name']
                insert_data('product', last_line_data)
            order.write({'state': 'done', 'account_move': move.id})

            if self and order.company_id.anglo_saxon_accounting:
                add_anglosaxon_lines(grouped_data, order.date_order, order.company_id.id)
            if move:  # In case no order was changed
                move.sudo().write({
                    'document_class_id': order.document_class_id.id,
                    'sii_document_number': order.sii_document_number,
                })
        return {
            'grouped_data': grouped_data,
            'move': move,
        }

    @api.model
    def check_folios(self, sii_document_number, sequence_id, res_id=False):
        Sequences = self.env['ir.sequence']
        #buscar si hay otro documento con el mismo folio
        #en caso de existir, devolver False 
        #obtener el siguiente numero disponible para que ese se asigne en el pos
        domain = [
            ('sii_document_number', '=', sii_document_number),
            ('sequence_id', '=', sequence_id),
            ]
        if res_id:
            domain.append(('id','!=',res_id))
        other_orders = self.search(domain, limit=1)
        folio_valid = not bool(other_orders)
        if not folio_valid:
            SQL = """
                SELECT sequence_id, MAX(sii_document_number) AS sii_document_number
                FROM pos_order
                WHERE sequence_id = %(sequence_id)s AND sii_document_number > 0
                GROUP BY sequence_id
            """
            self.env.cr.execute(SQL, {'sequence_id': sequence_id})
            for line in self.env.cr.dictfetchall():
                sequence = Sequences.browse(line['sequence_id'])
                sii_document_number = line['sii_document_number'] + 1
                # verificar que el siguiente numero este dentro del rango de folios de los CAF
                caf_files = sequence.get_caf_files(sii_document_number)
                if not caf_files:
                    raise UserError(_("No hay caf disponible para el documento %s folio %s. Por favor suba un CAF o solicite uno en el SII." % 
                                      (sequence.sii_document_class_id.name or sequence.name, sii_document_number)))
        return (folio_valid, sii_document_number)

    @api.multi
    def action_pos_order_paid(self):
        if self.test_paid():
            if self.sequence_id:
                if (not self.sii_document_number or self.sii_document_number == 0):
                    consumo_folio = self.sequence_id.next_by_id()
                    #boletas electronicas validar que el folio no este siendo usado en otro pedido
                    if self.sequence_id.correct_folios_automatic:
                        folio_valid, sii_document_number = self.check_folios(consumo_folio, self.sequence_id.id, self.id)
                        #si el folio no es valido, pasar el folio correcto
                        if not folio_valid:
                            consumo_folio = sii_document_number
                            self.sequence_id.number_next_actual = sii_document_number + 1
                    self.sii_document_number = consumo_folio
                elif not self.env.context.get('no_update_sequence'):
                    self.sequence_id.next_by_id()#consumo Folio
                if not self.env.context.get('no_update_sequence'):
                    # actualizar secuencias en session
                    self.session_id.set_next_document_number(False)
                if not self.sii_xml_request and self.document_class_id.dte:
                    self.do_validate()
        return super(POS, self).action_pos_order_paid()
    
    @api.model
    def create_from_ui(self, orders):
        order_ids = super(POS, self.with_context(no_update_sequence=True)).create_from_ui(orders)
        if order_ids:
            SQL = """
                SELECT session_id, sequence_id, MAX(sii_document_number) AS sii_document_number
                FROM pos_order
                WHERE sequence_id IS NOT NULL AND sii_document_number > 0
                    AND id IN %(order_ids)s
                GROUP BY session_id, sequence_id
            """
            self.env.cr.execute(SQL, {'order_ids': tuple(order_ids)})
            Sequences = self.env['ir.sequence']
            session_ids = []
            for line in self.env.cr.dictfetchall():
                Sequences.browse(line['sequence_id']).sudo().write({'number_next_actual': line['sii_document_number']+1})
                if line['session_id'] not in session_ids:
                    session_ids.append(line['session_id'])
            for session_id in session_ids:
                self.env['pos.session'].browse(session_id).set_next_document_number(False)
        return order_ids
    
    def _prepare_bank_statement_line_payment_values(self, data):
        payment_vals = super(POS, self)._prepare_bank_statement_line_payment_values(data)
        # de base se le pasa el secuencial del pedido, pero seria mejor pasar el numero de documento
        if self.sii_document_number:
            payment_vals['name'] = "%s: %s" % (self.sii_document_number, data.get('payment_name') or '')
        return payment_vals

    @api.multi
    def exento(self):
        exento = 0
        for l in self.lines:
            if l.tax_ids_after_fiscal_position.amount == 0:
                exento += l.price_subtotal
        return exento if exento > 0 else (exento * -1)

    @api.multi
    def action_print_report(self):
        """ Print NC
        """
        return self.env.ref('l10n_cl_dte_point_of_sale.action_report_pos_boleta_ticket').report_action(self)

    @api.multi
    def _get_printed_report_name(self):
        self.ensure_one()
        report_string = "%s %s" % (self.document_class_id.name, self.sii_document_number)
        return report_string

    @api.multi
    def get_invoice(self):
        return self.invoice_id
    
    def _prepare_stock_move_vals(self, line, order_picking, return_picking, picking_type, return_pick_type, location_id, destination_id):
        vals_move = super(POS, self)._prepare_stock_move_vals(line, order_picking, return_picking, picking_type, return_pick_type, location_id, destination_id)
        vals_move['precio_unitario'] = line.price_unit
        vals_move['discount'] = line.discount
        vals_move['move_line_tax_ids'] = [(6, 0, line.tax_ids_after_fiscal_position.ids)]
        return vals_move
    
    @api.multi
    def _action_create_invoice(self):
        '''
        Crear factura de los pedidos que aun no tienen factura
        En caso que la sesion este cerrada, enviar a conciliar pagos, xq ya no se haran automaticamente
        '''
        orders_to_reconcile = self.browse()
        for pos_order in self:
            pos_order.action_pos_order_invoice()
            pos_order.invoice_id.sudo().action_invoice_open()
            pos_order.account_move = pos_order.invoice_id.move_id
            #pedidos realizados en sesion cerrada, enviar a conciliar pagos con la factura
            if pos_order.session_id.state == 'closed':
                orders_to_reconcile |= pos_order
        if orders_to_reconcile:
            orders_to_reconcile.sudo()._reconcile_payments()
            orders_to_reconcile.sudo()._anglo_saxon_reconcile_valuation()
        return True
    
    @api.model
    def action_create_invoice(self):
        '''
        Buscar todos los pedidos que aun no han sido facturados y facturarlos
        '''
        for sii_code in [33, ]:
            orders = self.search([
                ('state', '!=', 'draft'),
                ('invoice_id', '=', False),
                ('sii_document_number', '!=', False),
                ('document_class_id.sii_code', '=', sii_code),
                ('mig_res_id', '=', False),
            ], order="sii_document_number")
            orders.with_context(skip_validation_invoice_pos=True)._action_create_invoice()
        return True
    
    def create_picking(self):
        for order in self:
            if order.session_id.config_id.create_picking or self.env.context.get('force_create_picking'):
                if order.session_id.config_id.create_picking_account_move:
                    super(POS, self).create_picking()
                else:
                    # pasar bandera para que no se cree asiento contable en los movimientos de stock
                    # en el modulo generic_stock_account se agrega esa funcionalidad
                    super(POS, self.with_context(skip_valuation_moves=True)).create_picking()
        return True
    
    @api.model
    def action_create_picking(self):
        orders = self.search([
            ('picking_id', '=', False),
            ('state', 'not in', ('draft', 'cancel')),
            ('mig_res_id', '=', False),
        ])
        total = len(orders)
        count = 0
        for order in orders.with_context(force_create_picking=True):
            count += 1
            _logger.info("Creando picking %s de %s, TPV: %s", count, total, order.session_id.config_id.display_name)
            order.create_picking()
        return True
    
    @api.model
    def action_timbre_orders(self):
        orders = self.search([
            ('sii_xml_dte', '=', False),
            ('sii_document_number', '!=', False),
            ('state', 'not in', ('draft', 'cancel')),
            ('mig_res_id', '=', False),
        ])
        total = len(orders)
        count = 0
        for order in orders.with_context(force_timbre=True):
            count += 1
            _logger.info("Timbrando Pedido %s de %s, TPV: %s, Folio: %s", count, total, order.session_id.config_id.display_name, order.sii_document_number)
            order.do_validate()
        return True
    
    @api.multi
    def _prepare_refund(self, current_session):
        vals = super(POS, self)._prepare_refund(current_session)
        sequence_credit_note = current_session.config_id.cn_sequence_id
        if not sequence_credit_note:
            raise UserError("Por favor defina Secuencia de Notas de Crédito en el PUNTO DE VENTA: %s" % (current_session.config_id.name))
        vals.update({
            'sequence_id': sequence_credit_note.id,
            'document_class_id': sequence_credit_note.sii_document_class_id.id,
            'sii_document_number': 0,
            'signature': False,
        })
        return vals
    
    @api.multi
    def getTotalDiscount(self):
        total_discount = 0
        for l in self.lines:
            total_discount += l._get_discount_total()
        return total_discount
    
    @api.multi
    def name_get(self):
        res = []
        for pos_order in self:
            if pos_order.sii_document_number:
                name = "%s" % (pos_order.sii_document_number)
            else:
                name = "%s" % (pos_order.pos_reference)
            res.append((pos_order.id, name))
        return res


class Referencias(models.Model):
    _name = 'pos.order.referencias'
    _description = 'Referencias de Pedidos POS' 

    origen = fields.Char(
            string="Origin",
        )
    sii_referencia_TpoDocRef = fields.Many2one(
            'sii.document_class',
            string="SII Reference Document Type",
        )
    sii_referencia_CodRef = fields.Selection(
            [
                    ('1', 'Anula Documento de Referencia'),
                    ('2', 'Corrige texto Documento Referencia'),
                    ('3', 'Corrige montos')
            ],
            string="SII Reference Code",
        )
    motivo = fields.Char(
            string="Motivo",
        )
    order_id = fields.Many2one(
            'pos.order',
            ondelete='cascade',
            index=True,
            copy=False,
            string="Documento",
        )
    fecha_documento = fields.Date(
            string="Fecha Documento",
            required=True,
        )
