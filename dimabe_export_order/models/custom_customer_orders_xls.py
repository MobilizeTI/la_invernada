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
            file_name = 'temp.xlsx'
            workbook = xlsxwriter.Workbook(file_name)
            if not self.for_year or self.for_year == 0:
                self.for_year = int(date.now.strftime('%Y'))
            sheet = workbook.add_worksheet('Pedidos Clientes')
            row = 0
            col = 0
            titles = [(1,'N° EMB'),(2,'F. Zarpe'),(3,'Sem ETD'),(4,'Cargar Hasta'),(5,'Sem Carga'),
                    (6,'Cliente'),(7,'País'),(8,'Contrato Interno'),(9,'Contrato Cliente'),(10,'N° Pedido Odoo'),
                    (11,'N° Despacho Odoo'),(12,'Estatus Producción'),(13,'Estatus Despacho'),(14,'Estado A. Calidad'),
                    (15,'F. Envío al cliente'),(16,'Especie'),(17,'Variedad'),(18,'Color'),(19,'Producto'),(20,'Calibre'),
                    (21,'Kilos'),(22,'Precio'),(23,'Monto'),(24,'N° Factura'),(25,'Cláusula'),(26,'Envase'),(27,'Modo de Carga'),
                    (28,'Etiqueta Cliente'),(29,'Marca'),(30,'Agente'),(31,'Comisión'),(32,'Valor Comisión'),(33,'Puerto de Carga'),
                    (34,'Puerto de Destino'),(35,'Destino Final'),(36,'Vía de Transporte'),(37,'Planta de Carga'),
                    (38,'Fecha y Hora Carga'),(39,'N° de Guía'),(40,'Nave / Viaje'),(41,'Naviera'),(42,'N° Booking'),
                    (43,'N° BL'),(44,'Stacking'),(45,'Cut Off Documental'),(46,'F. Real Zarpe'),(47,'F. Real Arribo'),
                    (48,'N° Container'),(49,'Tipo Container'),(50,'Terminal Portuario Origen'),(51,'Depósito Retiro'),
                    (52,'Valor Flete'),(53,'Valor Seguro'),(54,'FOB Total'),(55,'FOB /Kg'),(56,'Obs. Calidad'),
                    (57,'Comentarios'),(58,'N° DUS')]
            
            for title in titles:
                sheet.write(row, col, title[1])
                col += 1
            row += 1
            col = 0

            workbook.close()

            from_date = '{}/01/01/'.format(str(self.for_year))
            to_date = '{}/12/31'.format(str(self.for_year))
            
            
            #bold_format = workbook.add_format({'bold':True})
            orders = self.env['sale.order'].search([('confirmation_date','>=',from_date),('confirmation_date','<=',to_date)])
            #shipping_numbers = self.env['account.invoice'].search([('departure_date.strftime("%Y")','=',str(self.for_year))])
            #self.set_title(sheet, bold_format)

            with open(file_name, "rb") as file:
                file_base64 = base64.b64encode(file.read())

            file_name = 'Archivo de Pedidos - {}'.format(self.for_year)
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
         ('A1','N° EMB')
         ('B1','F. Zarpe')
         ('C1','Sem ETD')
         ('D1','Cargar Hasta')
         ('E1','Sem Carga')
         ('F1','Cliente')
         ('G1','País')
         ('H1','Contrato Interno')
         ('I1','Contrato Cliente')
         ('J1','N° Pedido Odoo')
         ('K1','Estatus Producción')
         ('L1','Estatus Despacho')
         ('M1','Estado A. Calidad')
         ('N1','F. Envío al cliente')
         ('O1','Especie')
         ('P1','Variedad')
         ('Q1','Color')
         ('R1','Producto')
         ('S1','Calibre')
         ('T1','Kilos')
         ('U1','Precio')
         ('V1','Monto')
         ('W1','N° Factura')
         ('X1','Cláusula')
         ('Y1','Envase')
         ('Z1','Modo de Carga')
         ('AA1','Etiqueta Cliente')
         ('AB1','Marca')
         ('AC1','Agente')
         ('AD1','Comisión')
         ('AE1','Valor Comisión')
         ('AF1','Puerto de Carga')
         ('AG1','Puerto de Destino')
         ('AH1','Destino Final')
         ('AI1','Vía de Transporte')
         ('AJ1','Planta de Carga')
         ('AK1','Fecha y Hora Carga')
         ('AL1','N° de Guía')
         ('AM1','Nave / Viaje')
         ('AN1','Naviera')
         ('AO1','N° Booking')
         ('AP1','N° BL')
         ('AQ1','Stacking')
         ('AR1','Cut Off Documental')
         ('AS1','F. Real Zarpe')
         ('AT1','F. Real Arribo')
         ('AU1','N° Container')
         ('AV1','Tipo Container')
         ('AW1','Terminal Portuario Origen')
         ('AX1','Depósito Retiro')
         ('AY1','Valor Flete')
         ('AZ1','Valor Seguro')
         ('BA1','FOB Total')
         ('BB1','FOB /Kg')
         ('BC1','Obs. Calidad')
         ('BD1','Comentarios')
         ('BE1','N° DUS')
            