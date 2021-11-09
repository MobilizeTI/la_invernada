# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime, timedelta, date
from lxml import etree
import pytz
import logging
_logger = logging.getLogger(__name__)

from six import string_types
try:
    from facturacion_electronica import facturacion_electronica as fe
except Exception as e:
    _logger.warning("Problema al cargar Facturación electrónica: %s" % str(e))
try:
    from io import BytesIO
except:
    _logger.warning("no se ha cargado io")
try:
    import pdf417gen
except ImportError:
    _logger.info('Cannot import pdf417gen library')
try:
    import base64
except ImportError:
    _logger.info('Cannot import base64 library')
try:
    from PIL import Image, ImageDraw, ImageFont
except:
    _logger.warning("no se ha cargado PIL")



class stock_picking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def get_xml_file(self):
        return {
            'type' : 'ir.actions.act_url',
            'url': '/download/xml/guia/%s' % (self.id),
            'target': 'self',
        }

    def get_folio(self):
        # saca el folio directamente de la secuencia
        return int(self.sii_document_number)

    def pdf417bc(self, ted, columns=13, ratio=3):
        bc = pdf417gen.encode(
            ted,
            security_level=5,
            columns=columns,
            encoding='ISO-8859-1',
        )
        image = pdf417gen.render_image(
            bc,
            padding=15,
            scale=1,
            ratio=ratio,
        )
        return image

    @api.multi
    def get_barcode_img(self, columns=13, ratio=3):
        barcodefile = BytesIO()
        image = self.pdf417bc(self.sii_barcode, columns, ratio)
        image.save(barcodefile, 'PNG')
        data = barcodefile.getvalue()
        return base64.b64encode(data)

    def _get_barcode_img(self):
        for r in self:
            if r.sii_barcode:
                r.sii_barcode_img = r.get_barcode_img()

    sii_batch_number = fields.Integer(
        copy=False,
        string='Batch Number',
        readonly=True,
        help='Batch number for processing multiple invoices together')
    sii_barcode = fields.Char(
        copy=False,
        string=_('SII Barcode'),
        readonly=True,
        help='SII Barcode Name')
    sii_barcode_img = fields.Binary(
        compute="_get_barcode_img",
        string=_('SII Barcode Image'),
        help='SII Barcode Image in PDF417 format')
    sii_message = fields.Text(
            string='SII Message',
            copy=False,
        )
    sii_xml_dte = fields.Text(
            string='SII XML DTE',
            copy=False,
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
                ('EnCola','En cola de envío'),
                ('Enviado', 'Enviado'),
                ('Aceptado', 'Aceptado'),
                ('Rechazado', 'Rechazado'),
                ('Reparo', 'Reparo'),
                ('Proceso', 'Proceso'),
                ('Anulado', 'Anulado'),
            ],
            string='Resultado',
            copy=False,
            help="SII request result",
            default = '',
        )
    canceled = fields.Boolean(string="Is Canceled?")
    estado_recep_dte = fields.Selection(
        [
            ('no_revisado', 'No Revisado'),
            ('0', 'Conforme'),
            ('1', 'Error de Schema'),
            ('2', 'Error de Firma'),
            ('3', 'RUT Receptor No Corresponde'),
            ('90', 'Archivo Repetido'),
            ('91', 'Archivo Ilegible'),
            ('99', 'Envio Rechazado - Otros')
        ],string="Estado de Recepción del Envío")
    estado_recep_glosa = fields.Char(string="Información Adicional del Estado de Recepción")
    responsable_envio = fields.Many2one('res.users')
    document_class_id = fields.Many2one(
        'sii.document_class',
        string="Document Type",
        related="location_id.sii_document_class_id",
    )
    dte_ticket = fields.Boolean(
        string="¿Formato Ticket?")

    @api.multi
    def action_done(self):
        res = super(stock_picking, self).action_done()
        for s in self:
            if not s.use_documents or s.location_id.restore_mode:
                continue
            if not s.sii_document_number and s.location_id.sequence_id.is_dte:
                s.sii_document_number = s.location_id.sequence_id.next_by_id()
                document_number = (s.document_class_id.doc_code_prefix or '') + s.sii_document_number
                s.name = document_number
            if s.picking_type_id.code in ['outgoing', 'internal']:# @TODO diferenciar si es de salida o entrada para internal
                s.responsable_envio = self.env.uid
                s.sii_result = 'NoEnviado'
                s._timbrar()
                self.env['sii.cola_envio'].create({
                            'company_id': s.company_id.id,
                            'doc_ids': [s.id],
                            'model': 'stock.picking',
                            'user_id': self.env.uid,
                            'tipo_trabajo': 'pasivo',
                            'date_time': (datetime.now() + timedelta(hours=12)),
                        })
        return res

    @api.multi
    def do_dte_send_picking(self, n_atencion=None):
        ids = []
        if not isinstance(n_atencion, string_types):
            n_atencion = ''
        for rec in self:
            rec.responsable_envio = self.env.uid
            if rec.sii_result in ['', 'NoEnviado', 'Rechazado']:
                if not rec.sii_xml_request or rec.sii_result in [ 'Rechazado' ]:
                    rec._timbrar(n_atencion)
                    if len(rec.sii_xml_request.picking_ids) == 1:
                        rec.sii_xml_request.unlink()
                    else:
                        rec.sii_xml_request = False
                rec.sii_result = "EnCola"
                rec.sii_message = ""
                ids.append(rec.id)
        if ids:
            self.env['sii.cola_envio'].create({
                        'doc_ids': ids,
                        'model':'stock.picking',
                        'user_id':self.env.uid,
                        'tipo_trabajo':'envio',
                        'n_atencion': n_atencion,
                        "set_pruebas": self._context.get("set_pruebas", False),
                })

    def _giros_emisor(self):
        giros_emisor = []
        for ac in self.location_id.acteco_ids:
            giros_emisor.append(ac.code)
        return giros_emisor

    def _id_doc(self, taxInclude=False, MntExe=0):
        IdDoc = {}
        IdDoc['TipoDTE'] = self.document_class_id.sii_code
        IdDoc['Folio'] = self.get_folio()
        IdDoc['FchEmis'] = fields.Datetime.context_timestamp(
            self.with_context(tz='America/Santiago'),
            fields.Datetime.from_string(self.scheduled_date)
        ).strftime(DF)
        if self.transport_type and self.transport_type not in ['0']:
            IdDoc['TipoDespacho'] = self.transport_type
        IdDoc['IndTraslado'] = self.move_reason
        if self.dte_ticket:
            IdDoc['TpoImpresion'] = "T"
        if taxInclude and MntExe == 0 :
            IdDoc['MntBruto'] = 1
        #IdDoc['FmaPago'] = self.forma_pago or 1
        #IdDoc['FchVenc'] = self.date_due or datetime.strftime(datetime.now(), '%Y-%m-%d')
        return IdDoc

    def _emisor(self):
        Emisor = {}
        Emisor['RUTEmisor'] = self.company_id.partner_id.rut()
        Emisor['RznSoc'] = self.company_id.partner_id.name
        Emisor['GiroEmis'] = self.company_id.activity_description.name
        Emisor['Telefono'] = self.company_id.phone or ''
        Emisor['CorreoEmisor'] = self.company_id.dte_email_id.name_get()[0][1]
        Emisor['Actecos'] = self._giros_emisor()
        dir_origen = self.company_id
        if self.location_id.sii_code:
            Emisor['CdgSIISucur'] = self.location_id.sii_code
            dir_origen = self.location_id.sucursal_id.partner_id
        Emisor['DirOrigen'] = dir_origen.street + ' ' +(dir_origen.street2 or '')
        Emisor['CmnaOrigen'] = dir_origen.city_id.name or ''
        Emisor['CiudadOrigen'] = dir_origen.city or ''
        Emisor["Modo"] = "produccion" if self.company_id.dte_service_provider == 'SII'\
                  else 'certificacion'
        Emisor["NroResol"] = self.company_id.dte_resolution_number
        Emisor["FchResol"] = self.company_id.dte_resolution_date
        Emisor["ValorIva"] = 19
        return Emisor

    def _receptor(self):
        Receptor = {}
        partner_id = self.partner_id or self.company_id.partner_id
        if not partner_id.commercial_partner_id.vat :
            raise UserError("Debe Ingresar RUT Receptor")
        Receptor['RUTRecep'] = partner_id.rut()
        Receptor['RznSocRecep'] = partner_id.commercial_partner_id.name
        activity_description = self.activity_description or partner_id.activity_description
        if not activity_description:
            if self.partner_id.commercial_partner_id.acteco_ids:
                activity_description = self.partner_id.commercial_partner_id.acteco_ids[0]
            else:
                raise UserError(_('Seleccione giro del partner'))
        Receptor['GiroRecep'] = activity_description.name
        if partner_id.commercial_partner_id.phone:
            Receptor['Contacto'] = partner_id.commercial_partner_id.phone
        if partner_id.commercial_partner_id.dte_email:
            Receptor['CorreoRecep'] = partner_id.commercial_partner_id.dte_email
        if not partner_id.commercial_partner_id.street:
            raise UserError("Debe Ingresar Dirección Receptor")
        Receptor['DirRecep'] = (partner_id.commercial_partner_id.street) + ' ' + ((partner_id.commercial_partner_id.street2) or '')
        Receptor['CmnaRecep'] = partner_id.commercial_partner_id.city_id.name
        Receptor['CiudadRecep'] = partner_id.commercial_partner_id.city
        return Receptor

    def _transporte(self):
        Transporte = {}
        if self.patente:
            Transporte['Patente'] = self.patente[:8]
        elif self.vehicle:
            Transporte['Patente'] = self.vehicle.license_plate or ''
        if self.transport_type in ['2', '3'] and self.chofer:
            if not self.chofer.vat:
                raise UserError("Debe llenar los datos del chofer")
            if self.transport_type == '2':
                Transporte['RUTTrans'] = self.company_id.partner_id.rut()
            else:
                if not self.carrier_id.partner_id.vat:
                    raise UserError("Debe especificar el RUT del transportista, en su ficha de partner")
                Transporte['RUTTrans'] = self.carrier_id.partner_id.rut()
            if self.chofer:
                Transporte['Chofer'] = {}
                Transporte['Chofer']['RUTChofer'] = self.chofer.rut()
                Transporte['Chofer']['NombreChofer'] = self.chofer.name[:30]
        partner_id = self.partner_id or self.partner_id.commercial_partner_id or self.company_id.partner_id
        Transporte['DirDest'] = (partner_id.street or '')+ ' '+ (partner_id.street2 or '')
        Transporte['CmnaDest'] = partner_id.city_id.name or ''
        Transporte['CiudadDest'] = partner_id.city or ''
        #@TODO SUb Area Aduana
        return Transporte

    def _totales(self, MntExe=0, no_product=False, taxInclude=False):
        Totales = {}
        IVA = 19
        for line in self.move_lines:
            if line.move_line_tax_ids:
                for t in line.move_line_tax_ids:
                    if t.sii_code in [14, 15]:
                        IVA = t.amount
        if IVA > 0 and not no_product:
            Totales['MntNeto'] = int(round(self.amount_untaxed, 0))
            Totales['TasaIVA'] = round(IVA,2)
            Totales['IVA'] = int(round(self.amount_tax, 0))
        monto_total = int(round(self.amount_total, 0))
        if no_product:
            monto_total = 0
        Totales['MntTotal'] = monto_total
        return Totales

    def _encabezado(self, MntExe=0, no_product=False, taxInclude=False):
        Encabezado = {}
        Encabezado['IdDoc'] = self._id_doc(taxInclude, MntExe)
        Encabezado['Receptor'] = self._receptor()
        Encabezado['Transporte'] = self._transporte()
        Encabezado['Totales'] = self._totales(MntExe, no_product)
        return Encabezado

    def _picking_lines(self):
        line_number = 1
        picking_lines = []
        MntExe = 0
        for line in self.move_lines:
            no_product = False
            if line.product_id.default_code == 'NO_PRODUCT':
                no_product = True
            lines = {}
            lines['NroLinDet'] = line_number
            if line.product_id.default_code and not no_product:
                lines['CdgItem'] = {}
                lines['CdgItem']['TpoCodigo'] = 'INT1'
                lines['CdgItem']['VlrCodigo'] = line.product_id.default_code
            taxInclude = False
            lines["Impuesto"] = []
            if line.move_line_tax_ids:
                for t in line.move_line_tax_ids:
                    if t.sii_code in [26, 27, 28, 35, 271]:#@Agregar todos los adicionales
                        lines['CodImpAdic'] = t.sii_code
                    taxInclude = t.price_include
                    if t.amount == 0 or t.sii_code in [0]:#@TODO mejor manera de identificar exento de afecto
                        lines['IndExe'] = 1
                        MntExe += int(round(line.subtotal, 0))
                    else:
                        amount = t.amount
                        if t.sii_code in [28, 35]:
                            amount = t.compute_factor(line.product_uom)
                        lines["Impuesto"].append(
                                {
                                    "CodImp": t.sii_code,
                                    'price_include': taxInclude,
                                    'TasaImp': amount,
                                }
                        )
            lines['NmbItem'] = line.product_id.name
            lines['DscItem'] = line.name
            if line.product_id.default_code:
                lines['NmbItem'] = line.product_id.name.replace('['+line.product_id.default_code+'] ','')
            qty = round(line.quantity_done, 4)
            if qty <=0:
                qty = round(line.product_uom_qty, 4)
                if qty <=0:
                    raise UserError("¡No puede ser menor o igual que 0!, tiene líneas con cantidad realiada 0")
            if not no_product:
                lines['QtyItem'] = qty
            if self.move_reason in ['5']:
                no_product = True
            if not no_product:
                lines['UnmdItem'] = line.product_uom.name[:4]
                if line.precio_unitario > 0:
                    lines['PrcItem'] = round(line.precio_unitario, 4)
            if line.discount > 0:
                lines['DescuentoPct'] = line.discount
                lines['DescuentoMonto'] = int(round((((line.discount / 100) * lines['PrcItem'])* qty)))
            if not no_product:
                subtotal = line.subtotal if taxInclude else line.price_untaxed
                lines['MontoItem'] = int(round(subtotal, 0))
            if no_product:
                lines['MontoItem'] = 0
            line_number += 1
            picking_lines.append(lines)
            if 'IndExe' in lines:
                taxInclude = False
        if len(picking_lines) == 0:
            raise UserError(_('No se puede emitir una guía sin líneas'))
        return {
                'Detalle': picking_lines,
                'MntExe': MntExe,
                'no_product':no_product,
                'tax_include': taxInclude,
                }

    def _dte(self, n_atencion=None):
        dte = {}
        if self.canceled and self.sii_xml_request:
            dte['Anulado'] = 2
        elif self.canceled:
            dte['Anulado'] = 1
        picking_lines = self._picking_lines()
        dte['Encabezado'] = self._encabezado(
            picking_lines['MntExe'],
            picking_lines['no_product'],
            picking_lines['tax_include'])
        lin_ref = 1
        ref_lines = []
        if n_atencion and self._context.get("set_pruebas", False):
            ref_line = {}
            ref_line['NroLinRef'] = lin_ref
            ref_line['TpoDocRef'] = "SET"
            ref_line['FolioRef'] = self.get_folio()
            ref_line['FchRef'] = datetime.strftime(datetime.now(), '%Y-%m-%d')
            ref_line['RazonRef'] = "CASO "+n_atencion+"-" + str(self.sii_batch_number)
            lin_ref = 2
            ref_lines.append(ref_line)
        for ref in self.reference:
            if ref.sii_referencia_TpoDocRef.sii_code in ['33','34']:#@TODO Mejorar Búsqueda
                inv = self.env["account.invoice"].search([('sii_document_number','=',str(ref.origen))])
            ref_line = {}
            ref_line['NroLinRef'] = lin_ref
            if  ref.sii_referencia_TpoDocRef:
                ref_line['TpoDocRef'] = ref.sii_referencia_TpoDocRef.sii_code
                ref_line['FolioRef'] = ref.origen
                ref_line['FchRef'] = datetime.strftime(datetime.now(), '%Y-%m-%d')
                if ref.date:
                    ref_line['FchRef'] = ref.date
            ref_lines.append(ref_line)
            lin_ref += 1
        dte['Detalle'] = picking_lines['Detalle']
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

    def _timbrar(self, n_atencion=None):
        folio = self.get_folio()
        datos = self._get_datos_empresa(self.company_id)
        datos['Documento'] = [{
            'TipoDTE': self.document_class_id.sii_code,
            'caf_file': [self.location_id.sequence_id.get_caf_file(folio, decoded=False).decode()],
            'documentos': [self._dte(n_atencion)]
            },
        ]
        _logger.info('LOG: -->>> datos {}'.format(datos))
        date_obj = datos['Emisor']['FchResol']
        date_str = date_obj.strftime("%Y-%m-%d")
        datos['Emisor']['FchResol'] = date_str

        result = fe.timbrar(datos)
        if result[0].get('error'):
            raise UserError(result[0].get('error'))
        self.write({
            'sii_xml_dte': result[0]['sii_xml_request'],
            'sii_barcode': result[0]['sii_barcode'],
        })
        return True

    def _crear_envio(self, n_atencion=False, RUTRecep="60803000-K"):
        grupos = {}
        count = 0
        company_id = False
        batch = 0
        for r in self.with_context(lang='es_CL'):
            batch += 1
            if not r.sii_batch_number or r.sii_batch_number == 0:
                r.sii_batch_number = batch #si viene una guía/nota regferenciando una factura, que por numeración viene a continuación de la guia/nota, será recahazada laguía porque debe estar declarada la factura primero
            if (
                self._context.get("set_pruebas", False) or r.sii_result == "Rechazado" or not r.sii_xml_dte
            ):
                r._timbrar(n_atencion)
            grupos.setdefault(r.document_class_id.sii_code, [])
            grupos[r.document_class_id.sii_code].append({
                        'NroDTE': r.sii_batch_number,
                        'sii_xml_request': r.sii_xml_dte,
                        'Folio': r.get_folio(),
                })
            if r.sii_result in ["Rechazado"] or (
                self._context.get("set_pruebas", False) and r.sii_xml_request.state in ["", "draft", "NoEnviado"]
            ):
                if r.sii_xml_request:
                    if len(r.sii_xml_request.picking_ids) == 1:
                        r.sii_xml_request.unlink()
                    else:
                        r.sii_xml_request = False
                r.sii_message = ''
        datos = self[0]._get_datos_empresa(self[0].company_id)
        datos.update({
            'api': False,
            'Documento': []
        })
        for k, v in grupos.items():
            datos['Documento'].append(
                {
                    'TipoDTE': k,
                    'documentos': v,
                }
            )
        return datos

    @api.multi
    def do_dte_send(self, n_atencion=False):
        datos = self._crear_envio(n_atencion)
        envio_id = self[0].sii_xml_request
        if not envio_id:
            envio_id = self.env["sii.xml.envio"].create({
                'name': 'temporal',
                'xml_envio': 'temporal',
                'picking_ids': [[6,0, self.ids]],
                })
        datos["ID"] = "Env%s" %envio_id.id
        result = fe.timbrar_y_enviar(datos)
        envio = {
                'xml_envio': result.get('sii_xml_request', "temporal"),
                'name': result.get("sii_send_filename", "temporal"),
                'company_id': self[0].company_id.id,
                'user_id': self.env.uid,
                'sii_send_ident': result.get('sii_send_ident'),
                'sii_xml_response': result.get('sii_xml_response'),
                'state': result.get('status'),
            }
        envio_id.write(envio)
        return envio_id

    def _get_dte_status(self):
        datos = self[0]._get_datos_empresa(self[0].company_id)
        datos['Documento'] = []
        docs = {}
        for r in self:
            if r.sii_xml_request.state not in ['Aceptado', 'Rechazado']:
                continue
            docs.setdefault(r.document_class_id.sii_code, [])
            docs[r.document_class_id.sii_code].append(r._dte())
        if not docs:
            return
        for k, v in docs.items():
            datos['Documento'].append ({
                'TipoDTE': k,
                'documentos': v
            })
        resultado = fe.consulta_estado_documento(datos)
        if not resultado:
            _logger.warning("no resultado en picking")
            return
        for r in self:
            id = "T{}F{}".format(r.document_class_id.sii_code,
                                 r.sii_document_number)
            r.sii_result = resultado[id]['status']
            if resultado[id].get('xml_resp'):
                r.sii_message = resultado[id].get('xml_resp')

    @api.multi
    def ask_for_dte_status(self):
        for r in self:
            if not r.sii_xml_request and not r.sii_xml_request.sii_send_ident:
                raise UserError('No se ha enviado aún el documento, aún está en cola de envío interna en odoo')
            if r.sii_xml_request.state not in ['Aceptado', 'Rechazado']:
                r.sii_xml_request.with_context(
                    set_pruebas=self._context.get("set_pruebas", False)).get_send_status(r.env.user)
        try:
            self._get_dte_status()
        except Exception as e:
            _logger.warning("Error al obtener DTE Status Guía: %s" % str(e))

    @api.multi
    def _get_printed_report_name(self):
        self.ensure_one()
        if self.document_class_id:
            string_state = ""
            if self.state == 'draft':
                string_state = "en borrador "
            report_string = "%s %s %s" % (self.document_class_id.name,
                                          string_state,
                                          self.sii_document_number or '')
        else:
            report_string = super(AccountInvoice, self)._get_printed_report_name()
        return report_string

    @api.multi
    def getTotalDiscount(self):
        total_discount = 0
        for l in self.move_lines:
            qty = l.quantity_done
            if qty <= 0:
                qty = l.product_uom_qty
            total_discount +=  (((l.discount or 0.00) /100) * l.precio_unitario * qty)
        return self.currency_id.round(total_discount)

    @api.multi
    def sii_header(self):
        W, H = (560, 255)
        img = Image.new('RGB', (W, H), color=(255,255,255))

        d = ImageDraw.Draw(img)
        w, h = (0, 0)
        for i in range(10):
            d.rectangle(((w, h), (550+w, 220+h)), outline="black")
            w += 1
            h += 1
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 40)
        d.text((50,30), "R.U.T.: %s" % self.company_id.document_number, fill=(0,0,0), font=font)
        d.text((50,90), "Guía de Despacho", fill=(0,0,0), font=font)
        d.text((100,150), "Electrónica", fill=(0,0,0), font=font)
        d.text((220,210), "N° %s" % self.sii_document_number, fill=(0,0,0), font=font)
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20)
        d.text((200,235), "SII %s" %self.company_id.sii_regional_office_id.name, fill=(0,0,0), font=font)

        buffered = BytesIO()
        img.save(buffered, format="PNG")
        imm = base64.b64encode(buffered.getvalue()).decode()
        return imm

datos = {
    'Emisor': {
        'RUTEmisor': '76991487-0', 
        'RznSoc': 'Servicios La Invernada SPA', 
        'GiroEmis': 'Servicios', 
        'Telefono': '+56227603340', 
        'CorreoEmisor': 'lainvernada.dte2@gmail.com', 
        'Actecos': ['11101'], 
        'DirOrigen': 'Valle Hermoso, Camino San Miguel, Parcela N° 2 ', 
        'CmnaOrigen': 'Paine', 
        'CiudadOrigen': 'Paine', 
        'Modo': 'certificacion', 
        'NroResol': '0', 
        'FchResol': datetime.date(2021, 11, 5), 
        'ValorIva': 19}, 
    'firma_electronica': {
        'priv_key': '-----BEGIN PRIVATE KEY-----\nMIICdwIBADANBgkqhkiG9w0BAQEFAASCAmEwggJdAgEAAoGBAJ5Tfo0gblRXE8tU\n9FlhhY+u1ZUF6sLOid4inUtkCBUJaNtwkQ33pGtzmUme46PxDzVMn1tfDpUOCVZn\nBk47wH92IX1XLNjoIw2Q1KyILi1ylDxpCUHKjjs4y9PETs8/OR85tnSIAPM/gRlk\n3QkGK2R3SEusbh0XXyExYTiiYbRdAgMBAAECgYBHu2N4VEu4aZVdx9lHT7BgF2HM\nOViSN1puardiS2mAAnngBiGqNttnFYJLQTI4+kQeLV972db1AF2JqHbKZjcBslSO\nMGdVFIbukl7emnQTctjJJp6AFbx4rBdr0Rv0hLhWkNvxw3Nr1Jd3IlueBXdG8wAX\ntoVh2K+7/YthD4RsrwJBAMZhqiDvVf919R553HD090dJBy57NDruRVvfuxnsuMX9\n3CahOZmKgpGcaOT5OGso8/kqpiz2fmzd2HkrxZkaO18CQQDMT5QyOO3XP00xEloZ\nkkQbVT5dP1FbFFHaCrMrqufWVY9f+/ER+4SgHzUTunqoyNEl79vr5Jy62MVzogNS\nRmXDAkEAxX3W22DIsT/h3Qwd64nDXoESGDDpBz3LaLIrVpy2Oc0GzKI2cGdWotUe\nC80bYHrtnwDZW+usYn7cEY0E8u0NawJBAJd2k23cCG6fThGIAmWcqoL84fvs+dok\nqT2U2xkPXUnnKiBFPYVQShUOraGPiGliXrLaK9aoJ4zZMSA1RnMTH1MCQBTa6dQ+\nX8//ORhFL3M2ckIZp5CiRjeVFMP2sM7IRcBMdpxLhkJMimKfA6sku41iq8axebAk\nJCwy3rbDeUZojGk=\n-----END PRIVATE KEY-----\n', 
        'cert': '-----BEGIN CERTIFICATE-----\nMIIGXzCCBUegAwIBAgIKGZ9rgQAAAA3qxTANBgkqhkiG9w0BAQUFADCB0jELMAkG\nA1UEBhMCQ0wxHTAbBgNVBAgTFFJlZ2lvbiBNZXRyb3BvbGl0YW5hMREwDwYDVQQH\nEwhTYW50aWFnbzEUMBIGA1UEChMLRS1DRVJUQ0hJTEUxIDAeBgNVBAsTF0F1dG9y\naWRhZCBDZXJ0aWZpY2Fkb3JhMTAwLgYDVQQDEydFLUNFUlRDSElMRSBDQSBGSVJN\nQSBFTEVDVFJPTklDQSBTSU1QTEUxJzAlBgkqhkiG9w0BCQEWGHNjbGllbnRlc0Bl\nLWNlcnRjaGlsZS5jbDAeFw0xOTA1MjIyMzUxMzhaFw0yMjA1MjEyMzUxMzhaMIHg\nMQswCQYDVQQGEwJDTDEqMCgGA1UECAwhUkVHScOTTiBNRVRST1BPTElUQU5BIERF\nIFNBTlRJQUdPMREwDwYDVQQHEwhTYW50aWFnbzEdMBsGA1UEChMUTkFaQVIgQUND\nT1VOVElORyBTUEExHDAaBgNVBAsTE0FTRVNPUklBUyBDT05UQUJMRVMxJjAkBgNV\nBAMTHURBVklEIEVEVUFSRE8gVkFMRU5aVUVMQSBMSVJBMS0wKwYJKoZIhvcNAQkB\nFh5TQVJBTkNJQklBQE5BWkFSQUNDT1VOVElORy5DT00wgZ8wDQYJKoZIhvcNAQEB\nBQADgY0AMIGJAoGBAJ5Tfo0gblRXE8tU9FlhhY+u1ZUF6sLOid4inUtkCBUJaNtw\nkQ33pGtzmUme46PxDzVMn1tfDpUOCVZnBk47wH92IX1XLNjoIw2Q1KyILi1ylDxp\nCUHKjjs4y9PETs8/OR85tnSIAPM/gRlk3QkGK2R3SEusbh0XXyExYTiiYbRdAgMB\nAAGjggKpMIICpTCCAU8GA1UdIASCAUYwggFCMIIBPgYIKwYBBAHDUgUwggEwMC0G\nCCsGAQUFBwIBFiFodHRwOi8vd3d3LmUtY2VydGNoaWxlLmNsL0NQUy5odG0wgf4G\nCCsGAQUFBwICMIHxHoHuAEUAbAAgAHIAZQBzAHAAbwBuAGQAZQByACAAZQBzAHQA\nZQAgAGYAbwByAG0AdQBsAGEAcgBpAG8AIABlAHMAIAB1AG4AIAByAGUAcQB1AGkA\ncwBpAHQAbwAgAGkAbgBkAGkAcwBwAGUAbgBzAGEAYgBsAGUAIABwAGEAcgBhACAA\nZABhAHIAIABpAG4AaQBjAGkAbwAgAGEAbAAgAHAAcgBvAGMAZQBzAG8AIABkAGUA\nIABjAGUAcgB0AGkAZgBpAGMAYQBjAGkA8wBuAC4AIABQAG8AcwB0AGUAcgBpAG8A\ncgBtAGUAbgB0AGUALDAdBgNVHQ4EFgQUnoYhE1vzjQ3+tgh3cbK63GroXXkwCwYD\nVR0PBAQDAgTwMCMGA1UdEQQcMBqgGAYIKwYBBAHBAQGgDBYKMTAyNzIzNTAtMzAf\nBgNVHSMEGDAWgBR44T6f0hKzejyNzTAOU7NDKQezVTA+BgNVHR8ENzA1MDOgMaAv\nhi1odHRwOi8vY3JsLmUtY2VydGNoaWxlLmNsL2VjZXJ0Y2hpbGVjYUZFUy5jcmww\nOgYIKwYBBQUHAQEELjAsMCoGCCsGAQUFBzABhh5odHRwOi8vb2NzcC5lY2VydGNo\naWxlLmNsL29jc3AwPQYJKwYBBAGCNxUHBDAwLgYmKwYBBAGCNxUIgtyDL4WTjGaF\n1Z0XguLcJ4Hv7DxhgcueFIaoglgCAWQCAQQwIwYDVR0SBBwwGqAYBggrBgEEAcEB\nAqAMFgo5NjkyODE4MC01MA0GCSqGSIb3DQEBBQUAA4IBAQCX7h3S5JHBT6vTH6ix\n6Bg738X9Dy2xkDfAmVlRQUis4t7NKobCFr0OlFmZMTFSeisqNLJlpmr4R/KN7raS\nAmuS5EcGyFlk16FA4WUT+2jjpPl5LWuwVnAwZq6AyL6T9l9n651gmKCkGARL+Dy9\n3kc4hUkN/QyoA5YVa8cBsAdsw7T08qK2BBeH4FT6ydSSEwRKAKM86XbPBpwa6B5B\nvY1rfUhjL+spdpqyIzzqYSD87QN5Hucz3bro8dC0MZomIVwL33QQDB+jnhcUsN3p\n6BbxplKy7xwbBjtR0NxXLdBOeuMgugxF2Z+TmD6+eNEkoz8+hxSsMbEU8XV23oNt\nHUjY\n-----END CERTIFICATE-----\n', 
        'rut_firmante': '10272350-3', 
        'init_signature': False
        }, 
    'Documento': [
        {
            'TipoDTE': 52, 
            'caf_file': ['PD94bWwgdmVyc2lvbj0iMS4wIj8+CjxBVVRPUklaQUNJT04+CjxDQUYgdmVyc2lvbj0iMS4wIj4KPERBPgo8UkU+NzY5OTE0ODctMDwvUkU+CjxSUz5TRVJWSUNJT1MgTEEgSU5WRVJOQURBIFNQQTwvUlM+CjxURD41MjwvVEQ+CjxSTkc+PEQ+MTwvRD48SD4xMDwvSD48L1JORz4KPEZBPjIwMjEtMTEtMDk8L0ZBPgo8UlNBUEs+PE0+cUhzK1ViM3B4YzJEK2UrYVdONThGSEc4bjZKMCsybE5FS29IR1hKbjM1amJyKzhPY3FVS0MvMlhIOFRIVGplWVU5WlBtd0s1eHYzZ0JoVDBTLzduWVE9PTwvTT48RT5Bdz09PC9FPjwvUlNBUEs+CjxJREs+MTAwPC9JREs+CjwvREE+CjxGUk1BIGFsZ29yaXRtbz0iU0hBMXdpdGhSU0EiPmhXTEVMSm9OSUNRd1FVc2R2QWRMUm5iV0RpbGlQMmZLdGo0L1VUaHdubmR4WEMvT0w2NEx3Qzc0bWcwbDcxY0V5c0pwSTh1ODBsVkZlRThsUHdFYTVBPT08L0ZSTUE+CjwvQ0FGPgo8UlNBU0s+LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlCT2dJQkFBSkJBS2g3UGxHOTZjWE5nL252bWxqZWZCUnh2SitpZFB0cFRSQ3FCeGx5WjkrWTI2L3ZEbktsCkNndjlseC9FeDA0M21GUFdUNXNDdWNiOTRBWVU5RXYrNTJFQ0FRTUNRSEJTS1l2VDhTNkpBcWFmdkRzKy9XTDIKZmIvQm8xSkdNMkJ4V2hEMjcrcGswcTh2U0lnZTdhMk5QR1lJZk1ydFhHSFN1UkgrOG8rQTJTVG53dUZDdXFzQwpJUURYdC90bFhYWE9vdEp6TGpwcG54ZE12NDhxZGwwYStya3lsN1dtNmRzL3dRSWhBTWZ4TEx4SkFOYmsxMGxZCmZhSit2RUVCaXcrSnB6TDFBMmUzQTZrUVA0K2hBaUVBajgvODdqNU9pY0hob2g3Um03OWszZFVLSEU3b3ZLY20KSWJwNUdmRTgxU3NDSVFDRlMzTW9NS3M1N2VUYmtGUEJxZExXQVFkZnNSb2grS3p2ejFmR0N0VUthd0loQUoxdgp1enl6UzM0dFVocThKM0IxUjFTZ2FOWjZQQlFUcnluNTdxamdrNjZGCi0tLS0tRU5EIFJTQSBQUklWQVRFIEtFWS0tLS0tCjwvUlNBU0s+Cgo8UlNBUFVCSz4tLS0tLUJFR0lOIFBVQkxJQyBLRVktLS0tLQpNRm93RFFZSktvWklodmNOQVFFQkJRQURTUUF3UmdKQkFLaDdQbEc5NmNYTmcvbnZtbGplZkJSeHZKK2lkUHRwClRSQ3FCeGx5WjkrWTI2L3ZEbktsQ2d2OWx4L0V4MDQzbUZQV1Q1c0N1Y2I5NEFZVTlFdis1MkVDQVFNPQotLS0tLUVORCBQVUJMSUMgS0VZLS0tLS0KPC9SU0FQVUJLPgo8L0FVVE9SSVpBQ0lPTj4K'], 
            'documentos': [
                {
                    'Encabezado': {
                        'IdDoc': {
                            'TipoDTE': 52, 
                            'Folio': 3, 
                            'FchEmis': '2021-11-09', 
                            'TipoDespacho': '2', 
                            'IndTraslado': '1'}, 
                        'Receptor': {
                            'RUTRecep': '76853633-3', 
                            'RznSocRecep': 'Mobilize SpA', 
                            'GiroRecep': 'servicios informáticos', 
                            'CorreoRecep': 'contacto@mobilize.cl', 
                            'DirRecep': 'Av. Calera de Tango P S/N ', 
                            'CmnaRecep': 'Calera de Tango', 
                            'CiudadRecep': 'Calera de Tango'}, 
                        'Transporte': {
                            'Patente': 'DHWH88', 
                            'RUTTrans': '76991487-0', 
                            'Chofer': {
                                'RUTChofer': '15759006-5', 
                                'NombreChofer': 'Felipe Angulo'
                                }, 
                            'DirDest': 'Av. Calera de Tango P S/N ', 
                            'CmnaDest': 'Calera de Tango', 
                            'CiudadDest': 'Calera de Tango'}, 
                        'Totales': {
                            'MntNeto': 0, 
                            'TasaIVA': 19, 
                            'IVA': 0, 
                            'MntTotal': 0}
                            }, 
                        'Detalle': [
                            {
                                'NroLinDet': 1, 
                                'CdgItem': {
                                    'TpoCodigo': 'INT1', 
                                    'VlrCodigo': 'AF00102'
                                    }, 
                                'Impuesto': [], 
                                'NmbItem': 'Pallet Certificado tabla junta', 
                                'DscItem': '[AF00102] Pallet Certificado tabla junta (153 x 120 cm)', 
                                'QtyItem': 1.0, 
                                'UnmdItem': 'Unid', 
                                'PrcItem': 100.0, 
                                'MontoItem': 100}], 
                                'Referencia': []}]}]}
