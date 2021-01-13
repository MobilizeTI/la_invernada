from odoo import models, fields, api
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

    #order_ids = fields.Many2many('sale.order')

    order_id = fields.Many2one('sale.order')

    #To Export
    other_coin = fields.Many2one('res.currency', string='Otra Moneda')

    exchange_rate_other_coin = fields.Float('Tasa de Cambio Otra Moneda')

    departure_port = fields.Many2one('custom.port','Puerto de Embarque')

    arrival_port = fields.Many2one('custom.port','Puerto de Desembarque')

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

    saf_amount = fields.Float(string="Seguro")

    @api.onchange('partner_id')
    @api.multi
    def _compute_partner_activity(self):
        for item in self:
            activities = []
            for activity in item.partner_id.economic_activities:
                activities.append(activity.id)
            item.partner_activity_id = activities

    def _get_sale_orders(self):
        order_ids = []
        order_lines = self.env['sale.order.line'].search([])
        for ol in order_lines:
            if ol.qty_delivered < ol.product_uom_qty:
                if ol.order_id not in order_ids:
                    order_ids.append(ol.order_id)
        #self.order_ids = self.env['sale.order'].search([])
        


    
    @api.multi
    def send_to_sii(self):
        order_ids = []
        order_lines = self.env['sale.order.line'].search([])
        for ol in order_lines:
            if ol.qty_delivered < ol.product_uom_qty:
                if ol.order_id not in order_ids:
                    order_ids.append(ol.order_id.id)
               # raise models.ValidationError('el id {} es apto por que pedido: {} y entregado: {} u orderid: {}'.format(ol.id,ol.product_uom_qty,ol.qty_delivered,ol.order_id))
        test = ''
        for asd in order_ids:
            test = test + str(asd) + '-'
        raise models.ValidationError(test)

        url = self.env.user.company_id.dte_url
        headers = {
            "apiKey" : self.env.user.company_id.dte_hash,
            "CustomerCode": self.env.user.company_id.dte_customer_code
        }
        invoice = {}

        #Main Validations
        self.validation_fields()
        

        if self.dte_type_id.code == "33" or self.dte_type_id.code == "39": #Factura electrónica y Boleta electrónica
            invoice = self.invoice_type()
       
        elif self.dte_type_id.code == "34": #Factura no afecta o exenta electrónica
            invoice = self.invoice_type()
       
        elif self.dte_type_id.code == "41":  #Boleta exenta electrónica
            invoice = self.receipt_exempt_type()

        elif self.dte_type_id.code == "43": #Liquidación factura electrónica
            invoice = self.invoice_liquidation_type()
        
        elif self.dte_type_id.code == "46":  #Factura de compra electrónica
            invoice = self.invoice_type()
       
        elif self.dte_type_id.code == "56": #Nota de débito electrónica
            if len(self.references) > 0:
                invoice = self.invoice_type()
            else:
                raise models.ValidationError('Para Nota de Débito electrónica debe agregar al menos una Referencia') 
       
        elif self.dte_type_id.code == "61": #Nota de crédito electrónica
            if len(self.references) > 0:
                invoice = self.invoice_type()
            else:
                raise models.ValidationError('Para Nota de Crédito electrónica debe agregar al menos una Referencia')
       
        elif self.dte_type_id.code == "110": #Factura de exportación electrónica
            self.other_coin = self.exchange_rate
            invoice = self.invoice_type()
       
        elif self.dte_type_id.code == "111": #Nota de débito de exportación electrónica
            if len(self.references) > 0:
                invoice = self.debit_note_invoice_export_type()
            else:
                raise models.ValidationError('Para Nota de Débito de exportación electrónica debe agregar al menos una Referencia')
       
        elif self.dte_type_id.code == "112": #Nota de crédito de exportación electrónica
            if len(self.references) > 0:
                invoice = self.credit_note_invoice_export_type()
            else:
                raise models.ValidationError('Para Nota de Crédito de exportación electrónica debe agregar al menos una Referencia')
       
        #Add Common Data
        invoice['createdDate'] = self.date_invoice.strftime("%Y-%m-%d")
        invoice['dteType'] = self.dte_type_id.code
        
        #Si es Boleta Electronica
        if self.dte_type_id.code == '39':
            invoice['serviceIndicator'] = self.ind_service
            invoice['netAmountIndicator'] = self.ind_net_amount

        invoice['transmitter'] =  {
                "EnterpriseRut": '76991487-0', #self.env.user.company_id.invoice_rut, #re.sub('[\.]','', "11.111.111-1"), #self.env.user.company_id.invoice_rut,
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
        raise models.ValidationError(json.dumps(invoice))

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

            
     
    def validation_fields(self):
        if not self.partner_id:
            raise models.ValidationError('Por favor selccione el Cliente')
        else:
            if not self.partner_id.invoice_rut:
                raise models.ValidationError('El Cliente {} no tiene Rut de Facturación'.format(self.partner_id.name))
        
        if not self.date_invoice:
            raise models.ValidationError('Debe Selccionar la Fecha de la Factura')
        
        if not self.date_due:
            raise models.ValidationError('Debe Selccionar la Fecha de Expiración')

        if not self.dte_type_id.code:
            raise models.ValidationError('Por favor seleccione el Tipo de Documento a emitir')

        if len(self.invoice_line_ids) == 0:
            raise models.ValidationError('Por favor agregar al menos un Producto')

        if not self.company_activity_id or not self.partner_activity_id:
            raise models.ValidationError('Por favor seleccione la Actividad de la Compañía y del Proveedor')

        if self.dte_type_id.code != "34" and self.dte_type_id.code != "41" and self.dte_type_id.code != "61": #Consultar si en NC y ND prdocuto sin impuesto
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
                raise models.ValidationError('El Total de Bultos {} no cuadra con la usma de los bultos {}'.format(int(self.total_packages),int(count_quantity)))
            if self.currency_id.code == self.other_coin.code:
                raise models.ValidationError('El tipo de Moneda y Otra Moneda no pueden ser iguales')


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
        #raise models.ValidationError('value: {}  value_str: {}  floor: {}'.format(value, value_str, floor(value)))
        if int(list_value[1]) < 5:
            return floor(value)
        else:
            return round(value)

    #Factura electrónica y #Nota de crédito/debito electrónica
    def invoice_type(self):
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
            invoice['transport'] = {
                "Aduana": {
                    "SaleModeCode": str(self.sale_method.code),
                    "SaleClauseCode":str(self.export_clause.code),
                    "SaleClauseTotal":str(self.total_export_sales_clause),
                    "TransportRoute":str(self.type_transport.code),
                    "OriginPortCode":str(self.departure_port.code),
                    "DestinyPortCode":str(self.arrival_port.code),
                    "Tara":str(self.tara),
                    "GrossWeight":str(self.gross_weight),
                    "NetWeight":str(self.net_weight),
                    "UnitTaraCode":str(self.uom_tara.code),
                    "UnitGrossWeightCode":str(self.uom_gross_weight.code),
                    "UnitNetWeightCode":str(self.uom_net_weight.code),
                    "TotalPackages": str(self.total_packages),
                    "Packages": packages_list,
                    "FreightAmount": str(self.freight_amount),
                    "SafeAmount":str(self.saf_amount),
                    "ReceiverCountryCode":str(self.receiving_country_dte.code),
                    "DestinyCountryCode":str(self.destiny_country_dte.code)
                }  
            }
            invoice['total'] = {
                "CoinType": str(self.currency_id.name),
                "exemptAmount": str(exemtAmount),
                "totalAmount": str(total_amount)
            }
            if self.other_coin:
                invoice['othercoin'] = {
                    "CoinType" : str(self.other_coin.name),
                    "ExemptAmount" : str(exemtAmount * self.exchange_rate_other_coin),
                    "Amount" : str(total_amount * self.exchange_rate_other_coin)
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

    @api.onchange('amount_total')
    def total_change_invoice_Export(self):
        self.total_invoice_Export


    def total_invoice_Export(self):
        if self.dte_type_id.code == "110":
            self.total_export_sales_clause = self.amount_total
            raise models.ValidationError('{}{}'.format(self.amount_total,self.total_export_sales_clause))
            

    #Factura de exportación electrónica
    def invoice_export_type(self):
        productLines = []
        lineNumber = 1
        typeOfExemptEnum = ""
        #Transporte

        for item in self.invoice_line_ids:
            haveExempt = False
            if (len(item.invoice_line_tax_ids) == 0 or (len(item.invoice_line_tax_ids) == 1 and item.invoice_line_tax_ids[0].id == 6)):
                haveExempt = True
                typeOfExemptEnum = item.exempt
            if haveExempt:
                productLines.append(
                    {
                        "LineNumber": str(lineNumber),
                        "ProductTypeCode": "EAN",
                        "ProductCode": str(item.product_id.default_code),
                        "ProductName": item.name,
                        "ProductQuantity": str(int(item.quantity)),
                        "ProductPrice": str(int(item.price_unit)),
                        "ProductDiscountPercent": "0",
                        "DiscountAmount": "0",
                        "Amount": str(int(item.price_subtotal)),
                        "HaveExempt": haveExempt,
                        "TypeOfExemptEnum": typeOfExemptEnum
                    }
                )
            else:
                productLines.append(
                    {
                        "LineNumber": str(lineNumber),
                        "ProductTypeCode": "EAN",
                        "ProductCode": str(item.product_id.default_code),
                        "ProductName": item.name,
                        "ProductQuantity": str(int(item.quantity)),
                        "ProductPrice": str(int(item.price_unit)),
                        "ProductDiscountPercent": "0",
                        "DiscountAmount": "0",
                        "Amount": str(int(item.price_subtotal))
                    }
                )
            lineNumber += 1
        invoice= {
            "expirationDate": self.date_due.strftime("%Y-%m-%d"),
            "paymentType": self.method_of_payment,
            "recipient": {
                "EnterpriseRut": re.sub('[\.]','', self.partner_id.invoice_rut),
                "EnterpriseAddressOrigin": self.partner_id.street,
                "EnterpriseCity": self.partner_id.city,
                "EnterpriseCommune": self.partner_id.state_id.name,
                "EnterpriseName": self.partner_id.name,
                "EnterpriseTurn": self.partner_activity_id.name
            },
            "total": {
                "currency": str(self.currency),
                "netAmount": str(self.amount_untaxed),
                "exemptAmount": "0",
                "taxRate": "19",
                "taxtRateAmount": str(self.amount_tax),
                "totalAmount": str(self.amount_total)
            },
            "lines": productLines
        }
        return invoice

