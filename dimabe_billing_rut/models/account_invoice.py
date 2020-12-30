from odoo import models, fields, api
import json
import requests
import inspect
from datetime import date
import re


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    dte_folio = fields.Text(string='Folio DTE')
    dte_type_id = fields.Many2one(
        'dte.type', string='Tipo Documento'
    )
    dte_xml = fields.Text("XML")
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

    dte_type = fields.Many2many('dte.type',compute = 'onchange_type')

    @api.onchange('partner_id')
    @api.multi
    def _compute_partner_activity(self):
        for item in self:
            activities = []
            for activity in item.partner_id.economic_activities:
                activities.append(activity.id)
            item.partner_activity_id = activities
    #eliminar
    @api.one
    def send_to_sii_old(self):
        # PARA COMPLETAR EL DOCUMENTO SE DEBE BASAR EN http://www.sii.cl/factura_electronica/formato_dte.pdf
        if not self.company_activity_id or not self.partner_activity_id:
            raise models.ValidationError('Por favor seleccione las actividades de la compañía y del proveedor')
        if not self.company_id.invoice_rut or not self.partner_id.invoice_rut:
            raise models.ValidationError('No se encuentra registrado el rut de facturación')

        if not self.dte_type_id:
            raise models.ValidationError('Por favor seleccione tipo de documento a emitir')
        if not self.company_activity_id or not self.partner_activity_id:
            raise models.ValidationError('Debe seleccionar el giro de la compañí y proveedor a utilizar')

        if self.dte_type_id.code is '110' and self.currency_id.name is not 'USD' and not self.exchange_rate:
            raise models.ValidationError(
                'Para emitir una factura de exportación la moneda debe ser en USD y debe tener una tasa de cambio')

        dte = {}
        dte["Encabezado"] = {}
        dte["Encabezado"]["IdDoc"] = {}
        # El Portal completa los datos del Emisor
        dte["Encabezado"]["IdDoc"] = {"TipoDTE": self.dte_type_id.code}
        # Si es Boleta de debe indicar el tipo de servicio, por defecto de venta de servicios
        if self.dte_type_id.code in ('39', 39):
            dte["Encabezado"]["IdDoc"]["IndServicio"] = 3

        if not self.dte_type_id.code in ('39', 39, 110):
            # Se debe inicar SOLO SI los valores indicados en el documento son con iva incluido
            dte["Encabezado"]["IdDoc"]["MntBruto"] = 1

        if self.dte_type_id.code is '110':
            dte["Encabezado"]["OtraMoneda"] = {
                'TpoMoneda': 'PESO CL',
                'TpoCambio': self.exchange_rate,
                'MntExeOtrMnda': round(self.amount_total * self.exchange_rate, 2),
                'MntTotOtrMnda': round(self.amount_total * self.exchange_rate, 2)
            }
            dte["Encabezado"]["Totales"] = {
                'TpoMoneda': 'DOLAR USA',
                'MntExe': self.amount_total,
                'MntTotal': self.amount_total
            }

        # EL CAMPO RUT DE FACTURACIÓN, debe corresponder al RUT de la Empresa
        dte["Encabezado"]["Emisor"] = {"RUTEmisor": self.company_id.invoice_rut.replace(".", "")}

        # EL CAMPO VAT o NIF Del Partner, debe corresponder al RUT , si es empresa extranjera debe ser 55555555-5
        dte["Encabezado"]["Receptor"] = {"RUTRecep": self.partner_id.invoice_rut.replace(".", ""),
                                         "RznSocRecep": self.partner_id.name,
                                         "DirRecep": self.partner_id.street + ' ' + self.partner_id.city,
                                         "CmnaRecep": self.partner_id.city,
                                         "GiroRecep": self.partner_activity_id.name}

        dte["Encabezado"]["IdDoc"]["TermPagoGlosa"] = self.comment or ''
        dte["Encabezado"]["IdDoc"]["Folio"] = '0'
        dte["Encabezado"]["IdDoc"]["FchEmis"] = str(date.today())
        dte["Detalle"] = []
        for line in self.invoice_line_ids:
            # El Portal Calculos los Subtotales
            ld = {'NmbItem': line.product_id.name,
                  'DscItem': '',
                  'QtyItem': round(line.quantity, 6),
                  'PrcItem': round(line.price_unit, 4)
                  }
            if line.product_id.default_code:
                ld['CdgItem'] = {"TpoCodigo": "INT1",
                                 "VlrCodigo": line.product_id.default_code}
            if line.discount:
                ld['DescuentoPct'] = round(line.discount, 2)
            dte["Detalle"].append(ld)
        referencias = []
        for reference in self.references:
            ref = {'TpoDocRef': reference.document_type_reference_id.code or 'SET',
                   'FolioRef': reference.folio_reference,
                   'FchRef': reference.document_date.__str__(),
                   'RazonRef': reference.reason}
            if reference.code_reference:
                ref['CodRef'] = reference.code_reference
            referencias.append(ref)
        if referencias:
            dte['Referencia'] = referencias
        # raise models.ValidationError(json.dumps(dte))
        self.send_dte(json.dumps(dte))

    

    #eliminar
    def send_dte(self, dte):
        url = self.company_id.dte_url
        rut_emisor = self.company_id.invoice_rut.replace(".", "").split("-")[0]
        hash = self.company_id.dte_hash
        auth = requests.auth.HTTPBasicAuth(hash, 'X')
        ssl_check = False
        # Api para Generar DTE
        apidte = '/dte/documentos/gendte?getXML=true&getPDF=true&getTED=png'
        emitir = requests.post(url + '/api' + apidte, dte, auth=auth, verify=ssl_check)
        if emitir.status_code != 200:
            raise Exception('Error al Temporal: ' + emitir.json())
        data = emitir.json()
        self.dte_folio = data.get('folio', None)
        self.dte_xml = data.get("xml", None)
        self.dte_pdf = data.get('pdf', None)
        self.ted = data.get("ted", None)
        fecha = data.get("fecha", None)
        total = data.get("total", None)
        self.pdf_url = "%s/dte/dte_emitidos/pdf/%s/%s/0/%s/%s/%s" % (
            url, self.dte_type_id.code, self.dte_folio, rut_emisor, fecha, total)

    #new

    #@api.onchange('type')
    #not worked
    @api.multi
    def onchange_type(self):
        if self.type:
            if 'refund' in self.type:
                types = self.env['dte.type'].search([('code','in',('56','61','111','112'))]) 
            else:
                types = self.env['dte.type'].search([('code','not in',('56','61','111','112'))]) 

            return types
    
    @api.multi
    def send_to_sii(self):
        url = self.env.user.company_id.dte_url
        headers = {
            "apiKey" : self.env.user.company_id.dte_hash,
            "CustomerCode": self.env.user.company_id.dte_customer_code
        }
        invoice = {}

        #Main Validations
        self.validation_fields()
        

        if self.dte_type_id.code == "33": #Factura electrónica
            invoice = self.invoice_type()
       
        elif self.dte_type_id.code == "34": #Factura no afecta o exenta electrónica
            invoice = self.invoice_exempt_type()
       
        elif self.dte_type_id.code == "39": #Boleta electrónica
            invoice = self.invoice_type()
       
        elif self.dte_type_id.code == "41":  #Boleta exenta electrónica
            invoice = self.receipt_exempt_type()

        elif self.dte_type_id.code == "43": #Liquidación factura electrónica
            invoice = self.invoice_liquidation_type()
        
        elif self.dte_type_id.code == "46":  #Factura de compra electrónica
            invoice = self.invoice_purchase_type()
       
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
            invoice = self.invoice_export_type()
       
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
        if self.dte_type_id == '39':
            invoice['serviceIndicator'] = self.ind_service
            invoice['netAmountIndicator'] = self.ind_net_amount

        invoice['transmitter'] =  {
                "EnterpriseRut": re.sub('[\.]','', "11.111.111-1"), #self.env.user.company_id.invoice_rut,
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
        if 'urlPdf' in Jrkeys  and 'filePdf' in Jrkeys and 'folio' in Jrkeys and 'fileXml' in Jrkeys:
            self.write({'pdf_url':jr['urlPdf']})
            self.write({'dte_pdf':jr['filePdf']})
            self.write({'dte_folio':jr['folio']})
            self.write({'dte_xml':jr['fileXml']})
      
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

        if len(self.references) > 10:
            raise models.ValidationError('Solo puede generar 20 Referencias')

        if len(self.observations_ids) > 10: 
            raise models.ValidationError('Solo puede generar 10 Observaciones')

            

    @api.onchange('dte_type_id')
    def on_change_dte_type_id(self):
        for item in self:
            if item.dte_type_id.code == '39':
                res = {
                    'attrs': {
                        'ind_service': [('invisible', '=', False)],
                        'ind_net_amount':  [('invisible', '=', False)]
                    }
                }
            else:
                res = {
                    'attrs': {
                        'ind_service' : [('invisible', '=', True)],
                        'ind_net_amount' : [('invisible', '=', True)]
                    }
                }
        return res


    #Factura electrónica y #Nota de crédito electrónica
    def invoice_type(self):
        productLines = []
        lineNumber = 1
        typeOfExemptEnum = ""                       
        exemtAmount = 0
        netAmount = 0
        countNotExempt = 0
        for item in self.invoice_line_ids:
            haveExempt = False

            if len(item.invoice_line_tax_ids) == 0 or (len(item.invoice_line_tax_ids) == 1 and item.invoice_line_tax_ids[0].id == 6):
                haveExempt = True
                typeOfExemptEnum = item.exempt
                if typeOfExemptEnum == '7':
                    raise models.ValidationError('El Producto {} al no tener impuesto seleccionado, debe seleccionar el tipo Exento'.format(item.name))
            
            if haveExempt:
                exemtAmount += int(item.price_subtotal)
                productLines.append(
                    {
                        "LineNumber": str(lineNumber),
                        "ProductTypeCode": "EAN",
                        "ProductCode": str(item.product_id.default_code),
                        "ProductName": item.name,
                        "ProductQuantity": str(item.quantity), #segun DTEmite no es requerido int
                        "UnitOfMeasure": str(item.uom_id.name),
                        "ProductPrice": str(), #segun DTEmite no es requerido int
                        "ProductDiscountPercent": "0",
                        "DiscountAmount": "0",
                        "Amount": str(int(item.price_subtotal)),
                        "HaveExempt": haveExempt,
                        "TypeOfExemptEnum": typeOfExemptEnum
                    }
                )
            else:
                netAmount += int(item.price_subtotal)
                productLines.append(
                    {
                        "LineNumber": str(lineNumber),
                        "ProductTypeCode": "EAN",
                        "ProductCode": str(item.product_id.default_code),
                        "ProductName": item.name,
                        "ProductQuantity": str(item.quantity),
                        "UnitOfMeasure": str(item.uom_id.name),
                        "ProductPrice": str(item.price_unit),
                        "ProductDiscountPercent": "0",
                        "DiscountAmount": "0",
                        "Amount": str(int(item.price_subtotal))
                    }
                )
            lineNumber += 1
        
        if self.partner_id.phone:
            recipientPhone = str(self.partner_id.phone)
        elif self.partner_id.mobile:
            recipientPhone = str(self.partner_id.mobile)
        else:
            recipientPhone = ''

        invoice= {
            "expirationDate": self.date_due.strftime("%Y-%m-%d"),
            "paymentType": int(self.method_of_payment),
            "recipient": {
                "EnterpriseRut": re.sub('[\.]','', self.partner_id.invoice_rut),
                "EnterpriseAddressOrigin": self.partner_id.street[0:60],
                "EnterpriseCity": self.partner_id.city,
                "EnterpriseCommune": self.partner_id.state_id.name,
                "EnterpriseName": self.partner_id.name,
                "EnterpriseTurn": self.partner_activity_id.name,
                "EnterprisePhone": recipientPhone
            },
            "total": {
                "netAmount": str(netAmount),
                "exemptAmount": str(exemtAmount),
                "taxRate": "19",
                "taxtRateAmount": str(int(self.amount_tax)),
                "totalAmount": str(int(netAmount + exemtAmount + self.amount_tax))
            },
            "lines": productLines,
        }
        return invoice

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

