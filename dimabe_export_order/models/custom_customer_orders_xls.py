import base64
import xlsxwriter
from datetime import date
from odoo import fields, models, api

class CustomCustomerOrdersXls(models.TransientModel):
    _name = 'custom.customer.orders.xls'

    orders_file = fields.Binary('Archivo de Pedidos')

    for_year = fields.Integer(string="Año")

    @api.multi
    def generate_orders_file(self):
            file_name = 'temp.xlsx'
            workbook = xlsxwriter.Workbook(file_name)
            #if not self.for_year or self.for_year == 0:
            #    self.for_year = int(date.now.strftime('%Y'))
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


            from_date = '{}/01/01'.format(str(self.for_year))
            to_date = '{}/12/31'.format(str(self.for_year))
            
            
            #bold_format = workbook.add_format({'bold':True})
            orders = self.env['sale.order'].sudo().search([('confirmation_date','>=',from_date),('confirmation_date','<=',to_date)])
            #shipping_numbers = self.env['account.invoice'].search([('departure_date.strftime("%Y")','=',str(self.for_year))])
            #self.set_title(sheet, bold_format)
            
            for order in orders:
                stock_picking_ids = self.env['stock.picking'].sudo().search([('sale_id','=',order.id)])
                for stock in stock_picking_ids:
                    #N° Embarque
                    sheet.write(row, col, stock.shipping_number if stock.shipping_number else '') 
                    col += 1
                    #Fecha de Zarpe
                    sheet.write(row, col, stock.departure_date if stock.departure_date.strftime("%d-%m-%Y") else '')
                    col += 1
                    #Semana ETD
                    sheet.write(row, col, stock.etd_week)
                    col += 1
                    #Cargar Hasta
                    sheet.write(row, col, stock.required_loading_date if stock.required_loading_date.strftime("%d-%m-%Y") else '')
                    col += 1
                    #Semana Carga
                    sheet.write(row, col, stock.required_loading_week)
                    col += 1
                    #Cliente
                    sheet.write(row, col, stock.partner_id.name if stock.partner_id.name else '')
                    col += 1
                    #Pais
                    sheet.write(row, col, stock.partner_id.country_id.name if stock.partner_id.country_id.name else '')
                    col += 1
                    #Contrato Interno
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Contrato Cliente
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #N° Pedido Odoo
                    sheet.write(row, col, order.name)
                    col += 1
                    #N° Stock Picking Odoo
                    sheet.write(row, col, stock.name)
                    col += 1
                    #Estatus Produccion
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Estatus Despacho
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Estatus Calidad
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Fecha Envio al Cliente
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Especie
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Variedad
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Color
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Producto
                    sheet.write(row, col, "pendiente")  
                    col += 1
                    #Calibre
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Kilos
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Precio
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Monto
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #N° Factura
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Cláusula
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Envase
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Modo de carga
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Etiqueta Cliente
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Marca
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Agente
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Comisión
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Valor Comisión
                    sheet.write(row, col, "pendiente")  
                    col += 1
                    #Puerto de Carga
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Puerto de Destino
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Destino Final
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Vía de Transporte
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Planta de Carga
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Fecha y Hora de Carga
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #N° de Guía
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Nave / Viaje
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Naviera
                    sheet.write(row, col, "pendiente")  
                    col += 1
                    #N° Booking
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #N° BL
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Stacking
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Cut Off Document
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Fecha Real de Zarpe
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Fecha Real Arribo
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #N° Container
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Tipo Container
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Terminal Portuario Origen
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Depósito Retiro
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Valor Seguro
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #FOB total
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #FOB / Kg
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Obs. Calidad
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #Comentarios
                    sheet.write(row, col, "pendiente")
                    col += 1
                    #N° DUS
                    sheet.write(row, col, "pendiente")
                    col += 1


                    row += 1
                    col = 0

            workbook.close()
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
            