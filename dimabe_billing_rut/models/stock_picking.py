from odoo import models, fields, api
import json
import requests
from datetime import date
import re
from pdf417 import encode, render_image, render_svg
import base64
from io import BytesIO 
from math import floor

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    dte_folio = fields.Text(string='Folio DTE')
    dte_type_id =  fields.Many2one(
        'dte.type', string = 'Tipo Documento'
    )
    dte_xml = fields.Text("XML")
    dte_xml_sii = fields.Text("XML SII")
    dte_pdf = fields.Text("PDF")
    ted = fields.Text("TED")
    pdf_url = fields.Text("URL PDF")

    partner_economic_activities = fields.Many2many('custom.economic.activity',related='partner_id.economic_activities')
    company_economic_activities = fields.Many2many('custom.economic.activity', related='company_id.economic_activities')
    partner_activity_id = fields.Many2one('custom.economic.activity', string='Actividad del Proveedor')
    company_activity_id = fields.Many2one('custom.economic.activity', string='Actividad de la Compañía')
    references = fields.One2many(
        'account.invoice.references',
        'invoice_id',
        string="Referencias",
        readonly=False,
        states={'draft': [('readonly', False)]},
    )

    method_of_payment = fields.Selection(
        [
            ('1', 'Contado'),
            ('2', 'Crédito'),
            ('3', 'Gratuito')
        ],
        string="Forma de pago",
        readonly=True,
        states={'draft': [('readonly', False)]},
        default='1',
    )

    observations_ids = fields.One2many('custom.invoice.observations','invoice_id',string='Observaciones')

    dispatch_type = fields.Selection([
            ('0', 'Sin Despacho'),
            ('1', 'Despacho por cuenta del receptor del documento'),
            ('2', 'Despacho por cuenta del emisor a instalaciones del cliente'),
            ('3', 'Despacho por cuenta del emisor a otras instalaciones')
            ], 'Tipo de Despacho', default='0')

    transfer_indication  = fields.Selection([
            ('0', 'Sin Translado'),
            ('1', 'Operación constituye venta'),
            ('2', 'Ventas por efectuar'),
            ('3', 'Consignaciones'),
            ('4', 'Entrega gratuita'),
            ('5', 'Traslados internos'),
            ('6', 'Otros traslados no venta'),
            ('7', 'Guía de devolución'),
            ], 'Tipo Translado', default='0')


    date_due = fields.Date(string="Fecha Vencimiento")

    net_amount = fields.Char(string="Neto")

    amount_tax = fields.Char(string="IVA")

    exempt_amount = fields.Char(string="Exento")

    total = fields.Char(string="Total")

    invoiced = fields.Boolean(string="Estado Facturación",default=False)

    valid_to_sii = fields.Boolean(string="Valido para SII")

    #Comex Embarque

    shipping_company = fields.Many2one(
        comodel_name='custom.shipping.company',
        string='Naviera'
    )

    ship = fields.Many2one(
        comodel_name='custom.ship',
        string='Nave'
    )

    ship_number = fields.Char(
        string='Viaje'
    )

    type_transport = fields.Many2one('custom.type.transport','Vía de Transporte')

    departure_port = fields.Many2one(
        comodel_name='custom.port',
        string='Puerto de Embarque'
    )

    arrival_port = fields.Many2one(
        comodel_name='custom.port',
        string='Puerto de Desembarque'
    )

    required_loading_date = fields.Datetime(
        'Fecha requerida de carga'
    )

    required_loading_week = fields.Integer(
        'Semana de Carga',
        compute='_compute_required_loading_week',
        store=True
    )

    etd = fields.Date(
        string='ETD',
        nullable=True
    )

    etd_month = fields.Integer(
        'Mes ETD',
        compute='_compute_etd_values',
        store=True
    )

    etd_week = fields.Integer(
        'Semana ETD',
        compute='_compute_etd_values',
        store=True
    )

    eta = fields.Date(
        string='ETA',
        nullable=True
    )

    departure_date = fields.Datetime('Fecha de zarpe')

    arrival_date = fields.Datetime('Fecha de arribo')

    #Comex Embarque Method

    @api.model
    @api.onchange('etd')
    @api.depends('etd')
    def _compute_etd_values(self):
        if self.etd:
            try:
                self.etd_month = self.etd.month
                _year, _week, _day_of_week = self.etd.isocalendar()
                self.etd_week = _week
            except:
                raise UserWarning('Error producido al intentar obtener el mes y semana de embarque')
        else:
            self.etd_week = None
            self.etd_month = None

    @api.model
    @api.onchange('required_loading_date')
    @api.depends('required_loading_date')
    def _compute_required_loading_week(self):
        if self.required_loading_date:
            try:
                year, week, day_of_week = self.required_loading_date.isocalendar()
                self.required_loading_week = week
            except:
                raise UserWarning('no se pudo establecer la semana de carga')
        else:
            self.required_loading_week = None

    @api.one
    @api.constrains('etd', 'eta')
    def _check_eta_greater_than_etd(self):
        if self.etd == False and self.eta:
            raise models.ValidationError('Debe ingresar el ETD')
        if self.eta and self.eta < self.etd:
            raise models.ValidationError('La ETA debe ser mayor al ETD')


    @api.onchange('partner_id')
    @api.multi
    def _compute_partner_activity(self):
        for item in self:
            activities = []
            for activity in item.partner_id.economic_activities:
                activities.append(activity.id)
            item.partner_activity_id = activities
    

    @api.one
    def send_to_sii(self):

        url = self.env.user.company_id.dte_url
        headers = {
            "apiKey" : self.env.user.company_id.dte_hash,
            "CustomerCode": self.env.user.company_id.dte_customer_code
        }
        invoice = {}
        productLines = []
        lineNumber = 1
        netAmount = 0
        exemtAmount = 0
        countNotExempt = 0
        

        #Main Validations
        self.validation_fields()

        move_line = []
        if self.is_multiple_dispatch:
            move_line = self.dispatch_line_ids
        else:
            move_line = self.move_ids_without_package

        for item in move_line:
            haveExempt = False
            
            price_unit =  item.sale_id.mapped('order_line').filtered(lambda a : a.product_id.id == item.product_id.id).price_unit
            amount = item.real_dispatch_qty * price_unit if self.is_multiple_dispatch else item.quantity_done * price_unit
            tax_ids = self.sale_id.mapped('order_line').filtered(lambda a : a.product_id.id == item.product_id.id).tax_id
            amount_tax = 0
            for tax in tax_ids:
                if int(tax.amount) == 19:
                    amount_tax += amount * (tax.amount / 100)
                    break

            if len(self.sale_id.mapped('order_line').filtered(lambda a : a.product_id.id == item.product_id.id).mapped('tax_id')) == 0:
                haveExempt = True

            if haveExempt:
                exemtAmount += amount
                productLines.append(
                    {
                        "LineNumber": str(lineNumber),
                        "ProductTypeCode": "EAN",
                        "ProductCode": str(item.product_id.default_code),
                        "ProductName": item.product_id.name,
                        "ProductQuantity": str(item.real_dispatch_qty) if self.is_multiple_dispatch else str(item.quantity_done), #segun DTEmite no es requerido int
                        "UnitOfMeasure": str(item.product_id.uom_id.name),
                        "ProductPrice": str(price_unit), #segun DTEmite no es requerido int
                        "ProductDiscountPercent": "0",
                        "DiscountAmount": "0",
                        "Amount": str(self.roundclp(item.real_dispatch_qty * price_unit if self.is_multiple_dispatch else item.quantity_done * price_unit)), #str(int(amount)),
                        "HaveExempt": haveExempt,
                        "TypeOfExemptEnum": "1" #agregar campo a sale.order.line igual que acoount.invoice.line
                    }
                )
            else:
                netAmount += self.roundclp(amount)
                productLines.append(
                    {
                        "LineNumber": str(lineNumber),
                        "ProductTypeCode": "EAN",
                        "ProductCode": str(item.product_id.default_code),
                        "ProductName": item.product_id.name,
                        "ProductQuantity": str(item.real_dispatch_qty) if self.is_multiple_dispatch else str(item.quantity_done),
                        "UnitOfMeasure": str(item.product_id.uom_id.name),
                        "ProductPrice": str(price_unit),
                        "ProductDiscountPercent": "0",
                        "DiscountAmount": "0",
                        "Amount": str(self.roundclp(item.real_dispatch_qty * price_unit if self.is_multiple_dispatch else item.quantity_done * price_unit)),
                    }
                )
            lineNumber += 1
        
        if self.partner_id.phone:
            recipientPhone = str(self.partner_id.phone)
        elif self.partner_id.mobile:
            recipientPhone = str(self.partner_id.mobile)
        else:
            recipientPhone = ''


        self.write({
            'net_amount': str(self.roundclp(netAmount)),
            'exempt_amount': str(self.roundclp(exemtAmount)),
            'amount_tax': str(self.roundclp(amount_tax)),
            'total': str(self.roundclp(netAmount + exemtAmount + self.sale_id.amount_tax))
        })
     

        invoice= {
            "dteType": self.dte_type_id.code,
            "createdDate": self.scheduled_date.strftime("%Y-%m-%d"),
            "expirationDate": self.date_due.strftime("%Y-%m-%d"), #No hay fecha de vencimiento
            "paymentType": int(self.method_of_payment),
            "dispatchType": str(self.dispatch_type),
            "transferIndication": str(self.transfer_indication),
            "transmitter": {
                "EnterpriseRut": re.sub('[\.]','', self.company_id.invoice_rut), #re.sub('[\.]','', "76.991.487-0"), #self.env.user.company_id.invoice_rut,
                "EnterpriseActeco": self.company_activity_id.code,
                "EnterpriseAddressOrigin": self.env.user.company_id.street,
                "EnterpriseCity": self.env.user.company_id.city,
                "EnterpriseCommune": str(self.env.user.company_id.state_id.name),
                "EnterpriseName": self.env.user.company_id.partner_id.name,
                "EnterpriseTurn": self.company_id.enterprise_turn,
                "EnterprisePhone": self.env.user.company_id.phone if self.env.user.company_id.phone else ''
            },
            "recipient": {
                "EnterpriseRut": re.sub('[\.]','', self.partner_id.invoice_rut),
                "EnterpriseAddressOrigin": self.partner_id.street[0:60],
                "EnterpriseCity": self.partner_id.city,
                "EnterpriseCommune": self.partner_id.state_id.name,
                "EnterpriseName": self.partner_id.name,
                "EnterpriseTurn": self.partner_id.enterprise_turn,
                "EnterprisePhone": recipientPhone
            },
            "total": {
                "netAmount": self.net_amount, 
                "exemptAmount": self.exempt_amount,
                "taxRate": "19",
                "taxtRateAmount": self.amount_tax,
                "totalAmount":self.total 
            },
            "lines": productLines,
        }
        
        # Add Refeences
        if self.references and len(self.references) > 0:
            refrenecesList = []
            line_reference_number = 1
            for item in self.references:
                refrenecesList.append(
                    {
                        "LineNumber": str(line_reference_number),
                        "DocumentType": str(item.document_type_reference_id.id),
                        "Folio": str(item.folio_reference),
                        "Date": str(item.document_date),
                        "Code": str(item.code_reference),
                        "Reason": str(item.reason)
                    }
                )
                line_reference_number += 1
            invoice['references'] = refrenecesList
        #Add Additionals
        if len(self.observations_ids) > 0:
            additionals = []
            for item in self.observations_ids:
                additionals.append(item.observations)
            invoice['additional'] =  additionals    


        r = requests.post(url, json=invoice, headers=headers)

        #raise models.ValidationError(json.dumps(invoice))
        jr = json.loads(r.text)
        Jrkeys = jr.keys()
        if 'urlPdf' in Jrkeys and 'filePdf' in Jrkeys and 'folio' in Jrkeys and 'fileXml' in Jrkeys and 'ted' in Jrkeys:
            self.write({'pdf_url':jr['urlPdf']})
            self.write({'dte_pdf':jr['filePdf']})
            self.write({'dte_folio':jr['folio']})
            self.write({'dte_xml':jr['fileXml']})
            self.write({'dte_xml_sii':jr['fileXmlSII']})

            cols = 12
            while True:
                try:
                    if cols == 31:
                        break
                    codes = encode(jr['ted'],cols)
                    image = render_image(codes, scale=5, ratio=2)
                    buffered = BytesIO()
                    image.save(buffered, format="JPEG")
                    img_str = base64.b64encode(buffered.getvalue())
                    self.write({'ted':img_str})
                    break
                except:
                    cols += 1
      
        if 'status' in Jrkeys and 'title' in Jrkeys:
            raise models.ValidationError('Status: {} Title: {} Json: {}'.format(jr['status'],jr['title'],json.dumps(invoice)))
        elif 'message' in Jrkeys:
            raise models.ValidationError('Advertencia: {} Json: {}'.format(jr['message'],json.dumps(invoice)))

    def roundclp(self, value):
        value_str = str(value)
        list_value = value_str.split('.')
        if len(list_value) > 1:
            decimal = int(list_value[1][0])
            if decimal == 0:
                raise models.ValidationError(int(value))
                return int(value)
            elif decimal < 5:
                return floor(value)
            else:
                return round(value)
        else:
            return value

    def validation_fields(self):

        valid_to_sii = False

        if not self.date_due:
            raise models.ValidationError('Por favor ingrese la Fecha de Vencimiento')
        if not self.partner_id:
            raise models.ValidationError('Por favor seleccione el Cliente')
        else:
            if not self.partner_id.invoice_rut:
                raise models.ValidationError('El Cliente {} no tiene Rut de Facturación'.format(self.partner_id.name))

        if not self.dte_type_id.code:
            raise models.ValidationError('Por favor seleccione el Tipo de Documento a emitir')

        if len(self.move_ids_without_package) == 0:
            raise models.ValidationError('Por favor agregar al menos un Producto')

        if not self.company_activity_id or not self.partner_activity_id:
            raise models.ValidationError('Por favor seleccione la Actividad de la Compañía y del Proveedor')

        if len(self.references) > 10:
            raise models.ValidationError('Solo puede generar 20 Referencias')

        if len(self.observations_ids) > 10: 
            raise models.ValidationError('Solo puede generar 10 Observaciones')

        valid_to_sii = True

        if valid_to_sii:
            self.valid_to_sii = valid_to_sii