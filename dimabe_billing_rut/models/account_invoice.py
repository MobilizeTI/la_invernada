from odoo import models, fields, api
from odoo.exceptions import ValidationError
import json
import requests
import inspect
from datetime import date
import re
from pdf417 import encode, render_image, render_svg
import xml.etree.ElementTree as ET
import base64
from io import BytesIO 
from math import floor


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    dte_folio = fields.Text(string='Folio DTE')
    dte_type_id = fields.Many2one(
        'dte.type', string='Tipo Documento'
    )

    
    dte_xml = fields.Text("XML")
    dte_xml_sii = fields.Text("XML SII")
    dte_pdf = fields.Text("PDF")
    ted = fields.Text("TED")
    pdf_url = fields.Text("URL PDF")

    partner_economic_activities = fields.Many2many('custom.economic.activity', related='partner_id.economic_activities')
    company_economic_activities = fields.Many2many('custom.economic.activity', related='company_id.economic_activities')
    partner_activity_id = fields.Many2one('custom.economic.activity', string='Actividad del Proveedor')
    company_activity_id = fields.Many2one('custom.economic.activity', string='Actividad de la Compañía')
    references = fields.One2many(
        'account.invoice.references',
        'invoice_id',
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
        default='1'
    )

    dte_code = fields.Char(
        invisible=True
    )

    ind_service = fields.Selection(
        [
            ('1','Boleta de Servicios Periódicos'),
            ('2','Boleta de Servicios Periódicos Domiciliarios.'),
            ('3','Boleta de Ventas y Servicios'),
            ('4','Boleta de Espectáculos emitida por cuenta de terceros.')
        ],
        string = "Tipo de Transacción"
        #dte_type_id={'39':[('invisible', False)]}
    )

    ind_net_amount = fields.Selection(
        [
            ('0','Líneas de Detalle en Montos Brutos'),
            ('2','Líneas de Detalle en Montos Netos')
        ],
        string="Indicador Monto Neto"
        #dte_type_id={'39':[('invisible', False)]}
    )

    custom_invoice_id = fields.Many2one('custom.invoice','Factura Recibida')

    observations_ids = fields.One2many('custom.invoice.observations','invoice_id',string='Observaciones')

    dte_type = fields.Many2many('dte.type')

    #Orders to Add in Invoice

    order_to_add_ids = fields.Many2one('sale.order',
        domain=[('invoice_status','=','to invoice')],
        string="Pedidos"
    )

    stock_picking_ids = fields.Many2one('stock.picking',
        string="Despachos"
    )

    order_to_add_id = fields.Integer(string="Despacho Id")

    #To Export
    other_coin = fields.Many2one('res.currency', string='Otra Moneda')

    exchange_rate_other_coin = fields.Float('Tasa de Cambio Otra Moneda')

    type_transport = fields.Many2one('custom.type.transport','Vía de Transporte')

    receiving_country_dte = fields.Many2one('custom.receiving.country.dte','País Receptor')

    destiny_country_dte = fields.Many2one('custom.receiving.country.dte','País Destino')

    sale_method = fields.Many2one('custom.sale.method','Modalidad de Venta')

    export_clause = fields.Many2one('custom.export.clause','Cláusula de Exportación')

    total_export_sales_clause = fields.Float(string="Valor Cláusula de Venta Exportación", default=0.00)

    total_packages = fields.Integer(string="Total Bultos")

    packages = fields.One2many('custom.package','invoice_id',string="Bultos")

    tara = fields.Float(string="Tara")

    gross_weight = fields.Float(string="Peso Bruto")

    net_weight = fields.Float(string="Peso Neto")

    uom_tara = fields.Many2one('custom.uom','Unidad de Medida Tara')

    uom_gross_weight = fields.Many2one('custom.uom','Unidad de Peso Bruto')

    uom_net_weight = fields.Many2one('custom.uom','Unidad de Peso Neto')

    freight_amount = fields.Float(string="Flete")

    safe_amount = fields.Float(string="Seguro")

    orders_to_invoice = fields.One2many(
        'custom.orders.to.invoice',
        'invoice_id')

    #COMEX
    total_value = fields.Float(
        'Valor Total',
        compute='_compute_total_value',
        store=True
    )

    value_per_kilogram = fields.Float(
        'Valor por kilo',
        compute='_compute_value_per_kilogram',
        store=True
    )

    shipping_number = fields.Integer('Número Embarque')

    contract_correlative = fields.Integer('corr')

    contract_correlative_view = fields.Char(
        'N° Orden',
        compute='_get_correlative_text'
    )

    agent_id = fields.Many2one(
        'res.partner',
        'Agente',
        domain=[('is_agent', '=', True)]
    )

    commission = fields.Float('Comisión')

    total_commission = fields.Float(
        'Valor Comisión',
        compute='_compute_total_commission'
    )

    charging_mode = fields.Selection(
        [
            ('piso', 'A Piso'),
            ('slip_sheet', 'Slip Sheet'),
            ('palet', 'Paletizado')
        ],
        'Modo de Carga'
    )

    booking_number = fields.Char('N° Booking')

    bl_number = fields.Char('N° BL')

    container_number = fields.Char('N° Contenedor')

    container_type = fields.Many2one(
        'custom.container.type',
        'Tipo de contenedor'
    )

    client_label = fields.Boolean('Etiqueta Cliente', default=False)

    client_label_file = fields.Binary(string='Archivo Etiqueta Cliente')

    is_dispatcher = fields.Integer(
        compute="get_permision"
    )
    
    remarks_comex = fields.Text('Comentarios Comex')

    #EMBARQUE
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

    departure_port = fields.Many2one(
        comodel_name='custom.port',
        string='Puerto de Embarque'
    )

    arrival_port = fields.Many2one(
        comodel_name='custom.port',
        string='Puerto de Desembarque'
    )

    required_loading_date = fields.Date(
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

    #Emarque Method
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


    #COMEX METHOD

    @api.onchange('order_to_add_ids')
    def onchange_order_to_add(self):
        self.order_to_add_id = self.order_to_add_ids.id

    @api.multi
    def get_permision(self):
        for i in self.env.user.groups_id:
            if i.name == "Despachos":
                self.is_dispatcher = 1
    
    @api.multi
    @api.depends('freight_amount', 'safe_amount')
    def _compute_total_value(self):
        print('')
        #list_price = []
        #list_qty = []
        #prices = 0
        #qantas = 0
        #if len(self.invoice_line_ids) > 0:
        #    for i in self.invoice_line_ids:
        #        list_price.append(i.price_unit * i.quantity)

            #for a in item.move_ids_without_package:
            #    if len(item.move_ids_without_package) != 0:
            #        list_qty.append(int(a.quantity_done))
            #        prices = sum(list_price)
            #        qantas = sum(list_qty)

            #item.total_value = (prices * qantas) + item.freight_value + item.safe_value
        #raise models.ValidationError('{} {} {}'.format(sum(list_price), self.freight_amount,  self.safe_amount))
        #self.total_value =  sum(list_price) + self.freight_amount + self.safe_amount
            

    @api.multi
    @api.depends('total_value')
    def _compute_value_per_kilogram(self):
        print('')
        #for item in self:
        #    qty_total = 0
         #   for line in item.move_ids_without_package:
          #      qty_total = qty_total + line.quantity_done
          #  if qty_total > 0:
          #      item.value_per_kilogram = item.total_value / qty_total

    @api.onchange('commission')
    @api.multi
    def _compute_total_commission(self):
        print('')
        #for item in self:
        #    if item.agent_id and item.commission > 3:
        #        raise models.ValidationError('la comisión debe ser mayor que 0 y menor o igual que 3')
        #    else:
        #        item.total_commission = (item.commission / 100) \
        #                         
                                        #* (sum(item.sale_id.order_line.mapped('price_unit'))
                                        #* sum(item.move_ids_without_package.mapped('product_uom_qty')))
    
    @api.multi
    # @api.depends('contract_id')
    def _get_correlative_text(self):
        print('')
        # if self.contract_id:
        # if self.contract_correlative == 0:
        # existing = self.contract_id.sale_order_ids.search([('name', '=', self.name)])
        # if existing:
        # self.contract_correlative = existing.contract_correlative
        # if self.contract_correlative == 0:
        # self.contract_correlative = len(self.contract_id.sale_order_ids)
        # else:
        # self.contract_correlative = 0
        # if self.contract_id.name and self.contract_correlative and self.contract_id.container_number:
        # self.contract_correlative_view = '{}-{}/{}'.format(
        # self.contract_id.name,
        # self.contract_correlative,
        # self.contract_id.container_number
        # )
        # else:
        # self.contract_correlative_view = ''
    

    @api.onchange('partner_id')
    @api.multi
    def _compute_partner_activity(self):
        for item in self:
            activities = []
            for activity in item.partner_id.economic_activities:
                activities.append(activity.id)
            item.partner_activity_id = activities
        
    @api.multi
    def send_to_sii(self):
        self.update_sale_order()
        #raise models.ValidationError('verificar actualizacion de SO')
        url = self.env.user.company_id.dte_url
        headers = {
            "apiKey" : self.env.user.company_id.dte_hash,
            "CustomerCode": self.env.user.company_id.dte_customer_code
        }
        invoice = {}
        self.validation_fields()
        invoice = self.generate_invoice()
       
        if self.dte_type_id.code == "41":  #Boleta exenta electrónica
            invoice = self.receipt_exempt_type()

        if self.dte_type_id.code == "43": #Liquidación factura electrónica
            invoice = self.invoice_liquidation_type()

        invoice['createdDate'] = self.date_invoice.strftime("%Y-%m-%d")
        invoice['dteType'] = self.dte_type_id.code
        
        #Si es Boleta Electronica
        if self.dte_type_id.code == '39':
            invoice['serviceIndicator'] = self.ind_service
            invoice['netAmountIndicator'] = self.ind_net_amount

        invoice['transmitter'] =  {
                "EnterpriseRut": re.sub('[\.]','', self.env.user.company_id.invoice_rut), #re.sub('[\.]','', "11.111.111-1"), #self.env.user.company_id.invoice_rut,
                "EnterpriseActeco": self.company_activity_id.code,
                "EnterpriseAddressOrigin": self.env.user.company_id.street,
                "EnterpriseCity": self.env.user.company_id.city,
                "EnterpriseCommune": str(self.env.user.company_id.state_id.name),
                "EnterpriseName": self.env.user.company_id.partner_id.name,
                "EnterpriseTurn": self.company_activity_id.name,
                "EnterprisePhone": self.env.user.company_id.phone if self.env.user.company_id.phone else ''
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
            
            #self.update_sale_order()
        
        if 'status' in Jrkeys and 'title' in Jrkeys:
            raise models.ValidationError('Status: {} Title: {} Json: {}'.format(jr['status'],jr['title'],json.dumps(invoice)))
        elif 'message' in Jrkeys:
            raise models.ValidationError('Advertencia: {} Json: {}'.format(jr['message'],json.dumps(invoice)))
  
    #pendiente
    def update_sale_order(self):
        if len(self.orders_to_invoice) > 0:
            list_order_ids = []
            for item in self.orders_to_invoice:
                if item.order_id not in list_order_ids:
                    list_order_ids.append(item.order_id)
            
            for item in list_order_ids:
                order = self.env['sale.order'].search([('id','=',item)])
                order.update({
                    'invoice_ids': [(4,item ,{self.id})]
                })
        #if len(self.invoice_line_ids) > 0: 
        #    for line in self.invoice_line_ids:
        #        sale_order = self.env['stock.picking'].search([('id', '=', line.stock_picking_id)])
        #        sum_quantity = 0

        #        sale_order_lines = self.env['sale.order.line'].search([('order_id', '=', line.order_id)])
        #        if len(sale_order_lines) > 0: 
        #            for s in sale_order_lines:
        #                if s.product_id.id == line.product_id.id:
        #                    new_qty_invoiced = s.qty_invoiced + line.quantity
        #                    s.write({
        #                        'qty_invoiced': new_qty_invoiced
        #                    })

     
    def validation_fields(self):
        if not self.partner_id:
            raise models.ValidationError('Por favor seleccione el Cliente')
        else:
            if not self.partner_id.invoice_rut:
                raise models.ValidationError('El Cliente {} no tiene Rut de Facturación'.format(self.partner_id.name))
        
        if not self.date_invoice:
            raise models.ValidationError('Debe Seleccionar la Fecha de la Factura')
        
        if not self.date_due:
            raise models.ValidationError('Debe Seleccionar el Plazo de Pago para obtener la Fecha de Expiración')

        if not self.dte_type_id.code:
            raise models.ValidationError('Por favor seleccione el Tipo de Documento a emitir')

        if len(self.invoice_line_ids) == 0:
            raise models.ValidationError('Por favor agregar al menos un Producto')

        if not self.company_activity_id or not self.partner_activity_id:
            raise models.ValidationError('Por favor seleccione la Actividad de la Compañía y del Proveedor')

        if self.dte_type_id.code != "34" and self.dte_type_id.code != "41" and self.dte_type_id.code != "61" and self.dte_type_id.code != "110": #Consultar si en NC y ND prdocuto sin impuesto
            countNotExempt = 0
            for item in self.invoice_line_ids:
                if len(item.invoice_line_tax_ids) > 0 and item.invoice_line_tax_ids[0].id != 6:
                    countNotExempt += 1
            if countNotExempt == 0:
                raise models.ValidationError('El tipo {} debe tener almenos un producto con impuesto'.format(self.dte_type_id.name))

        if self.dte_type_id.code == "33" or self.dte_type_id.code == "39":
            if self.currency_id.name != "CLP":
                raise models.ValidationError('El Tipo {} debe tener moneda CLP {}'.format(self.dte_type_id.name, self.currency_id.id))
        
        if self.dte_type_id.code == "110": #FACTURA EXPORTACION
            count_quantity = 0
            for pk in self.packages:
                count_quantity += pk.quantity
            if int(count_quantity) != int(self.total_packages):
                raise models.ValidationError('El Total de Bultos {} no cuadra con la suma de los bultos {}'.format(int(self.total_packages),int(count_quantity)))
            if not self.partner_id.country_id.sii_code:
                raise models.ValidationError('El País {} no tiene registrado el Código SII'.format(self.partner_id.country_id.name))
            if not self.currency_id.sii_currency_name:
                raise models.ValidationError('La Moneda {} no tiene registrado el Nombre SII'.format(self.currency_id.name))
            if not self.other_coin.sii_currency_name:
               raise models.ValidationError('La otra Moneda {} no tiene registrado el Nombre SII'.format(self.currency_id.name))


        if self.dte_type_id.code == "61" or self.dte_type_id.code == "111" or self.dte_type_id.code == "56" or self.dte_type_id.code == "112":
            if len(self.references) == 0:
                raise models.ValidationError('Para {} debe agregar al menos una Referencia'.format(self.dte_type_id.name))

        for item in self.invoice_line_ids:
            for tax_line in item.invoice_line_tax_ids:
                if (tax_line.id == 6 or tax_line.id == None) and (item.exempt == "7"):
                    raise models.ValidationError('El Producto {} no tiene impuesto por ende debe seleccionar el Tipo Exento'.format(item.name))
        
        if len(self.references) > 10:
            raise models.ValidationError('Solo puede generar 20 Referencias')

        if len(self.observations_ids) > 10: 
            raise models.ValidationError('Solo puede generar 10 Observaciones')

    @api.onchange('dte_type_id')
    def on_change_dte_type_id(self):
        self.dte_code = self.dte_type_id.code

    def roundclp(self, value):
        value_str = str(value)
        list_value = value_str.split('.')
        if int(list_value[1]) < 5:
            return floor(value)
        else:
            return round(value)

    def generate_invoice(self):
        productLines = []
        lineNumber = 1
        typeOfExemptEnum = ""                       
        exemtAmount = 0
        netAmount = 0
        countNotExempt = 0
        for item in self.invoice_line_ids:
            haveExempt = False

            if self.dte_type_id.code == "34": #FACTURA EXENTA
                haveExempt == True

            if haveExempt == False and (len(item.invoice_line_tax_ids) == 0 or (len(item.invoice_line_tax_ids) == 1 and item.invoice_line_tax_ids[0].id == 6)):
                haveExempt = True
                typeOfExemptEnum = item.exempt
                if typeOfExemptEnum == '7':
                    raise models.ValidationError('El Producto {} al no tener impuesto seleccionado, debe seleccionar el tipo Exento'.format(item.name))
            
            if haveExempt:
                if self.dte_type_id.code == "110": #Exportacion con decimal
                    amount_subtotal = item.price_subtotal
                else: 
                    amount_subtotal = self.roundclp(item.price_subtotal)
                
                exemtAmount += amount_subtotal

                productLines.append(
                    {
                        "LineNumber": str(lineNumber),
                        "ProductTypeCode": "EAN",
                        "ProductCode": str(item.product_id.default_code),
                        "ProductName": item.name,
                        "ProductQuantity": str(item.quantity), #segun DTEmite no es requerido int
                        "UnitOfMeasure": str(item.uom_id.name),
                        "ProductPrice": str(item.price_unit), #segun DTEmite no es requerido int
                        "ProductDiscountPercent": "0",
                        "DiscountAmount": "0",
                        "Amount": str(amount_subtotal),
                        "HaveExempt": haveExempt,
                        "TypeOfExemptEnum": typeOfExemptEnum
                    }
                )
            else:
                product_price = item.price_unit
                amount_subtotal = item.price_subtotal

                if self.dte_type_id.code == "110": #Exportacion con decimal
                    amount_subtotal = item.price_subtotal
                    netAmount += item.price_subtotal
                elif self.dte_type_id.code == "39" and self.ind_net_amount != "2": #Boleta Elecronica  CORREGIR Y CONSULAR
                    for tax in item.invoice_line_tax_ids:
                        if tax.id == 1 or tax.id == 2 or tax.id == 3 or tax.id == 4: 
                            product_price = item.price_unit  * (1 + tax.amount / 100)
                            amount_subtotal = self.roundclp(item.price_subtotal * (1 + tax.amount / 100))               
                else: 
                    amount_subtotal = self.roundclp(item.price_subtotal)
                    netAmount += self.roundclp(item.price_subtotal)
                productLines.append(
                    {
                        "LineNumber": str(lineNumber),
                        "ProductTypeCode": "EAN",
                        "ProductCode": str(item.product_id.default_code),
                        "ProductName": item.name,
                        "ProductQuantity": str(item.quantity),
                        "UnitOfMeasure": str(item.uom_id.name),
                        "ProductPrice": str(product_price),
                        "ProductDiscountPercent": "0",
                        "DiscountAmount": "0",
                        "Amount": str(amount_subtotal)
                    }
                )
            lineNumber += 1
        
        if self.partner_id.phone:
            recipientPhone = str(self.partner_id.phone)
        elif self.partner_id.mobile:
            recipientPhone = str(self.partner_id.mobile)
        else:
            recipientPhone = ''

        if self.dte_type_id.code == "110": #Factura Exportacion decimal
            total_amount = netAmount + exemtAmount + self.amount_tax
            if len(self.packages) > 0:
                packages_list =[]
                for pk in self.packages:
                    packages_list.append(
                    {
                        "PackageTypeCode": str(pk.package_type.code),
                        "PackageQuantity": str(int(pk.quantity)),
                        "Brands": str(pk.brand),
                        "Container": pk.container if str(pk.container) else '',
                        "Stamp": pk.container if str(pk.stamp) else ''
                    }
                )
        else:
            total_amount = self.roundclp(netAmount + exemtAmount + self.amount_tax)

        invoice= {
            "expirationDate": self.date_due.strftime("%Y-%m-%d"),
            "paymentType": str(int(self.method_of_payment)),
            "recipient": {
                "EnterpriseRut": re.sub('[\.]','', self.partner_id.invoice_rut),
                "EnterpriseAddressOrigin": self.partner_id.street[0:60],
                "EnterpriseCity": self.partner_id.city,
                "EnterpriseCommune": self.partner_id.state_id.name,
                "EnterpriseName": self.partner_id.name,
                "EnterpriseTurn": self.partner_activity_id.name,
                "EnterprisePhone": recipientPhone
            },
            "lines": productLines,
        }
        if self.dte_type_id.code == "110":
            invoice['recipient']['EnterpriseCountryCode'] = self.partner_id.country_id.sii_code
            invoice['transport'] = {
                "SaleModeCode": str(self.sale_method.code),
                "SaleClauseCode":str(self.export_clause.code),
                "SaleClauseTotal":str(self.total_export_sales_clause),
                "TransportRoute":str(self.type_transport.code),
                "OriginPortCode": str(self.departure_port.code),
                "DestinyPortCode": str(self.arrival_port.code),
                "Tara":str(self.tara),
                "GrossWeight":str(self.gross_weight),
                "NetWeight":str(self.net_weight),
                "UnitTaraCode":str(self.uom_tara.code),
                "UnitGrossWeightCode":str(self.uom_gross_weight.code),
                "UnitNetWeightCode":str(self.uom_net_weight.code),
                "TotalPackages": str(self.total_packages),
                "Packages": packages_list,
                "FreightAmount": str(self.freight_amount),
                "SafeAmount":str(self.safe_amount),
                "ReceiverCountryCode":str(self.receiving_country_dte.code),
                "DestinyCountryCode":str(self.destiny_country_dte.code)
            }
  
            #por confirmar  si el exento siempre es igual al total
            exemtAmount = total_amount

            if self.other_coin.id == 45: # Si es CLP el monto es int
                other_coin_amount = int(total_amount * self.exchange_rate_other_coin)
                other_coin_exempt = int(exemtAmount * self.exchange_rate_other_coin)
            else:
                other_coin_amount = total_amount * self.exchange_rate_other_coin
                other_coin_exempt = exemtAmount

            invoice['total'] = {
                "CoinType": str(self.currency_id.sii_currency_name),
                "exemptAmount": str(exemtAmount),
                "totalAmount": str(total_amount)
            }

            invoice['othercoin'] = {
                "CoinType" : str(self.other_coin.sii_currency_name),
                "ExemptAmount" : str(other_coin_exempt),
                "Amount" : str(other_coin_amount)
            }
            
        else:
            invoice['total'] = {
                "netAmount": str(netAmount),
                "exemptAmount": str(exemtAmount),
                "taxRate": "19",
                "taxtRateAmount": str(self.roundclp(self.amount_tax)),
                "totalAmount": str(total_amount)
            }
        return invoice

    #revisar
    @api.onchange('amount_total')
    def total_change_invoice_Export(self):
        self.total_invoice_Export


    def total_invoice_Export(self):
        if self.dte_type_id.code == "110":
            self.total_export_sales_clause = self.amount_total
            #raise models.ValidationError('{}{}'.format(self.amount_total,self.total_export_sales_clause))

    @api.multi  
    def add_products_by_order(self):
        if self.stock_picking_ids and self.order_to_add_ids:
            product_ids = self.env['sale.order.line'].search([('order_id','=',self.order_to_add_ids.id)])
            stock_picking_line = self.env['stock.move.line'].search([('picking_id','=',self.stock_picking_ids.id)])
            
            if len(product_ids) > 0:
                for item in product_ids: 
                    quantity = 0
                    for picking in stock_picking_line:
                        if picking.product_id.id == item.product_id.id:
                            quantity += picking.qty_done 
                    exist_to_invoice_line = False
                    exist_orders_to_invoice = False

                    if len(self.orders_to_invoice) > 0:
                        for o in self.orders_to_invoice:
                            if item.product_id.id == o.product_id and self.stock_picking_ids.id == o.stock_picking_id and self.order_to_add_ids.id == o.order_id:
                                exist_orders_to_invoice = True
                    
                    if len(self.invoice_line_ids) > 0:
                        for i in self.invoice_line_ids:
                            if item.product_id.id == i.product_id.id:
                                exist_to_invoice_line = True
                                i.write({
                                   'quantity': i.quantity + quantity
                                })

                    if not exist_to_invoice_line:
                        self.env['account.invoice.line'].create({
                            'name' : item.name,
                            'product_id': item.product_id.id,
                            'invoice_id': self.id,
                            'price_unit': item.price_unit,
                            'account_id': item.product_id.categ_id.property_account_income_categ_id.id,
                            'uom_id': item.product_uom.id,
                            'quantity': quantity
                        })
                    
                    if not exist_orders_to_invoice: #cambiar a not
                        self.env['custom.orders.to.invoice'].create({
                            'product_id': item.product_id.id,
                            'product_name': item.name,
                            'quantity_to_invoice': str(quantity),
                            'invoice_id': self.id,
                            'order_id': self.order_to_add_ids.id,
                            'order_name': self.order_to_add_ids.name,
                            'stock_picking_name': self.stock_picking_ids.name,
                            'stock_picking_id': self.stock_picking_ids.id,
                        })
                    else:
                       raise models.ValidationError('El Producto {} del despacho {} del pedido {} ya se ecuentra agregado'.format(item.product_id.name, self.stock_picking_ids.name, self.order_to_add_ids.name))

            else:
                raise models.ValidationError('No se han encontrado Productos')

        else:
            raise models.ValidationError('Debe Seleccionar El Pedido luego el N° Despacho para agregar productos a la lista')

    #modificar 
    @api.onchange('orders_to_invoice')
    @api.multi
    def change_orders_to_invoice(self):
        for line in self.invoice_line_ids:
            sum_quantity = 0
            for item in self.orders_to_invoice:
                if line.product_id.id == item.product_id:
                    sum_quantity += float(item.quantity_to_invoice)
            if sum_quantity == 0: #por verifica
                line.unlink()
            elif sum_quantity != line.quantity: #validado
                line.write({
                    'quantity': sum_quantity
                })
            

    #Send Data to Stock_Picking Comex
    @api.multi
    def write(self, vals):
        order_list = []
        for item in self.orders_to_invoice:
            if item.order_id:
                order_list.append(item.stock_picking_id)
        
        stock_picking_ids = self.env['stock.picking'].search([('id', 'in', order_list)])
        res = super(AccountInvoice, self).write(vals)
        for s in stock_picking_ids:
            s.write({
                'shipping_number': self.shipping_number,
                'contract_correlative_view': self.contract_correlative_view,
                'agent_id': self.agent_id.id,
                'commission' : self.commission,
                'total_commission' : self.total_commission,
                'charging_mode' : self.charging_mode,
                'booking_number' : self.booking_number,
                'bl_number' : self.bl_number,
                'container_number' : self.container_number,
                'container_type' : self.container_type.id,
                'client_label' : self.client_label,
                'client_label_file': self.client_label_file,
                'freight_value' : self.freight_amount,
                'safe_value' : self.safe_amount,
                'total_value' : self.total_value,
                'value_per_kilogram' : self.value_per_kilogram,
                'remarks': self.remarks_comex,
                'shipping_company': self.shipping_company.id,
                'ship': self.ship.id,
                'ship_number': self.ship_number,
                'type_transport': self.type_transport.id,
                'departure_port': self.departure_port.id,
                'arrival_port': self.arrival_port.id,
                'required_loading_date': self.required_loading_date,
                'etd': self.etd,
                'eta': self.eta,
                'departure_date': self.departure_date,
                'arrival_date': self.arrival_date
            })
        return res
