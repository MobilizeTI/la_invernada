import base64
import xlsxwriter
from datetime import date
from odoo import fields, models, api

class CustomCustomerOrdersXls(models.TransientModel):
    _name = 'custom.customer.orders.xls'

    orders_file = fields.Binary('Archivo de Pedidos')

    for_year = fields.Integer('Año')

    @api.multi
    def generate_orders_file(self):
        for item in self:
            file_name = 'temp'
            workbook = xlsxwriter.Workbook(file_name)
            if not self.for_year or self.for_year == 0:
                self.for_year = int(date.now.strftime('%Y'))
            worksheet = workbook.add_worksheet('Pedidos Clientes')
            #formats = self.set_formats(workbook)
            row = 0
            col = 0
            bold_format = workbook.add_format({'bold':True})
            orders = self.env['sale.order'].search([('','',)])
            shipping_numbers = self.env['account.invoice'].search([('departure_date.strftime("%Y")','=',str(self.for_year))])
            self.set_title(worksheet, bold_format)

            with open(file_name, "rb") as file:
                file_base64 = base64.b64encode(file.read())

            file_name = 'Archivo de Pedidos {}'.format(self.for_year)
            attachment_id = self.env['ir.attachment'].sudo().create({
                'name': file_name,
                'datas_fname': file_name,
                'datas': file_base64
            })
            action = {
                'type': 'ir.actions.act_url',
                'url': '/web/content/{}?download=true'.format(attachment_id.id, ),
                'target': 'current',
            }
            return action




    
    def set_formats(self, workbook):
        merge_format_string = workbook.add_format({
            'border': 0,
            'align': 'center',
            'valign': 'vcenter',
        })
        merge_format_number = workbook.add_format({
            'bold': 0,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '#,##0'
        })
        merge_format_title = workbook.add_format({
            'border': 1,
            'bold': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        return {
            'string': merge_format_string,
            'number': merge_format_number,
            'title': merge_format_title
        }
    def set_title(self, sheet, format):
        sheet.write('A1','N° EMB',format)
        sheet.write('B1','F. Zarpe',format)
        sheet.write('C1','Sem ETD',format)
        sheet.write('D1','Cargar Hasta',format)
        sheet.write('E1','Sem Carga',format)
        sheet.write('F1','Cliente',format)
        sheet.write('G1','País',format)
        sheet.write('H1','Contrato Interno',format)
        sheet.write('I1','Contrato Cliente',format)
        sheet.write('J1','N° Pedido Odoo',format)
        sheet.write('K1','Estatus Producción',format)
        sheet.write('L1','Estatus Despacho',format)
        sheet.write('M1','Estado A. Calidad',format)
        sheet.write('N1','F. Envío al cliente',format)
        sheet.write('O1','Especie',format)
        sheet.write('P1','Variedad',format)
        sheet.write('Q1','Color',format)
        sheet.write('R1','Producto',format)
        sheet.write('S1','Calibre',format)
        sheet.write('T1','Kilos',format)
        sheet.write('U1','Precio',format)
        sheet.write('V1','Monto',format)
        sheet.write('W1','N° Factura',format)
        sheet.write('X1','Cláusula',format)
        sheet.write('Y1','Envase',format)
        sheet.write('Z1','Modo de Carga',format)
        sheet.write('AA1','Etiqueta Cliente',format)
        sheet.write('AB1','Marca',format)
        sheet.write('AC1','Agente',format)
        sheet.write('AD1','Comisión',format)
        sheet.write('AE1','Valor Comisión',format)
        sheet.write('AF1','Puerto de Carga',format)
        sheet.write('AG1','Puerto de Destino',format)
        sheet.write('AH1','Destino Final',format)
        sheet.write('AI1','Vía de Transporte',format)
        sheet.write('AJ1','Planta de Carga',format)
        sheet.write('AK1','Fecha y Hora Carga',format)
        sheet.write('AL1','N° de Guía',format)
        sheet.write('AM1','Nave / Viaje',format)
        sheet.write('AN1','Naviera',format)
        sheet.write('AO1','N° Booking',format)
        sheet.write('AP1','N° BL',format)
        sheet.write('AQ1','Stacking',format)
        sheet.write('AR1','Cut Off Documental',format)
        sheet.write('AS1','F. Real Zarpe',format)
        sheet.write('AT1','F. Real Arribo',format)
        sheet.write('AU1','N° Container',format)
        sheet.write('AV1','Tipo Container',format)
        sheet.write('AW1','Terminal Portuario Origen',format)
        sheet.write('AX1','Depósito Retiro',format)
        sheet.write('AY1','Valor Flete',format)
        sheet.write('AZ1','Valor Seguro',format)
        sheet.write('BA1','FOB Total',format)
        sheet.write('BB1','FOB /Kg',format)
        sheet.write('BC1','Obs. Calidad',format)
        sheet.write('BD1','Comentarios',format)
        sheet.write('BE1','N° DUS',format)
            