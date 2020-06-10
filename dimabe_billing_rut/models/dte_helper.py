import json
import requests
from datetime import date

class DteHelper():

    def __init__(self):
        
    
    def send_to_sii(self,model):
        #PARA COMPLETAR EL DOCUMENTO SE DEBE BASAR EN http://www.sii.cl/factura_electronica/formato_dte.pdf
        if not model.company_activity_id or not model.partner_activity_id:
            raise models.ValidationError('Por favor seleccione las actividades de la compañía y del proveedor')
        if not model.company_id.invoice_rut or not model.partner_id.invoice_rut:
            raise models.ValidationError('No se encuentra registrado el rut de facturación')

        if not model.dte_type_id:
            raise models.ValidationError('Por favor seleccione tipo de documento a emitir')
        if not model.company_activity_id or not model.partner_activity_id:
            raise models.ValidationError('Debe seleccionar el giro de la compañí y proveedor a utilizar')

        dte = {}
        dte["Encabezado"] = {}
        dte["Encabezado"]["IdDoc"] = {}
        # El Portal completa los datos del Emisor
        dte["Encabezado"]["IdDoc"] = {"TipoDTE": str(model.dte_type_id.code)}
        #Si es Boleta de debe indicar el tipo de servicio, por defecto de venta de servicios
        if model.dte_type_id.code in ('39', 39):
            dte["Encabezado"]["IdDoc"]["IndServicio"] = 3

        if not model.dte_type_id.code in ('39', 39):
            #Se debe inicar SOLO SI los valores indicados en el documento son con iva incluido
            dte["Encabezado"]["IdDoc"]["MntBruto"] = 1

        #EL CAMPO RUT DE FACTURACIÓN, debe corresponder al RUT de la Empresa
        dte["Encabezado"]["Emisor"] = {"RUTEmisor": model.company_id.invoice_rut.replace(".","")}

        # EL CAMPO VAT o NIF Del Partner, debe corresponder al RUT , si es empresa extranjera debe ser 55555555-5
        dte["Encabezado"]["Receptor"] = {"RUTRecep": model.partner_id.invoice_rut.replace(".",""),
                                         "RznSocRecep": model.partner_id.name,
                                         "DirRecep": model.partner_id.street +  ' ' + model.partner_id.city,
                                         "CmnaRecep": model.partner_id.city,
                                         "GiroRecep": model.partner_activity_id.name}
        
        dte["Encabezado"]["IdDoc"]["TermPagoGlosa"] = model.comment or ''
        dte["Encabezado"]["IdDoc"]["Folio"] = '0'
        dte["Encabezado"]["IdDoc"]["FchEmis"] = str(date.today())
        dte["Detalle"] = []
        for line in model.invoice_line_ids:
            #El Portal Calculos los Subtotales
            ld = {'NmbItem': line.product_id.name,
             'DscItem': '',
             'QtyItem': round(line.quantity, 6),
             'PrcItem': round(line.price_unit,4)
            }
            if line.product_id.default_code:
                ld['CdgItem'] = {"TpoCodigo": "INT1",
                              "VlrCodigo": line.product_id.default_code}
            if line.discount:
                ld['DescuentoPct']= round(line.discount,2)
            dte["Detalle"].append(ld)
        referencias = []
        for reference in model.references:
            ref = {'TpoDocRef':reference.document_type_reference or 'SET',
                   'FolioRef':reference.folio_reference,
                   'FchRef':reference.document_date.__str__(),
                   'RazonRef':reference.reason}
            if reference.code_reference:
                ref['CodRef'] =reference.code_reference
            referencias.append(ref)
        if referencias:
            dte['Referencia'] = referencias

        self.send_dte(json.dumps(dte))

    def send_dte(self, model, dte):
        url = model.company_id.dte_url
        rut_emisor = model.company_id.invoice_rut.replace(".", "").split("-")[0]
        hash = model.company_id.dte_hash
        auth = requests.auth.HTTPBasicAuth(hash, 'X')
        ssl_check = False
        # Api para Generar DTE
        apidte = '/dte/documentos/gendte?getXML=true&getPDF=true&getTED=png'
        emitir = requests.post(url + '/api' + apidte, dte, auth=auth, verify=ssl_check)
        if emitir.status_code != 200:
            raise Exception('Error al Temporal: ' + emitir.json())
        data = emitir.json()
        model.dte_folio = data.get('folio', None)
        model.dte_xml = data.get("xml", None)
        model.dte_pdf = data.get('pdf', None)
        model.ted = data.get("ted", None)
        fecha = data.get("fecha", None)
        total = data.get("total", None)
        model.pdf_url = "%s/dte/dte_emitidos/pdf/%s/%s/0/%s/%s/%s" % (url, model.dte_type_id.code, model.dte_folio, rut_emisor, fecha, total)


