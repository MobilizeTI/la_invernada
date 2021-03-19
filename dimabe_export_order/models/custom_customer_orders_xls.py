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
            formats = self.set_formats(workbook)
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
                sheet.write(row, col, title[1], formats['title'])
                col += 1
            row += 1
            col = 0
            
            from_date = '{}/01/01'.format(str(self.for_year))
            to_date = '{}/12/31'.format(str(self.for_year))
            
            #orders = self.env['sale.order'].sudo().search([('confirmation_date','>=',from_date),('confirmation_date','<=',to_date)])
            orders = self.env['sale.order'].sudo().search([('create_date','>=',from_date),('create_date','<=',to_date)])
            total_kilogram = 0
            total_amount = 0
            total_commission = 0
            total_bl = 0 #counter
            total_container = 0 # counter
            total_freight = 0
            total_safe = 0
            total_fob = 0
            total_fob_per_kilo = 0

            if len(orders) > 0:
                for order in orders:
                    stock_picking_ids = self.env['stock.picking'].sudo().search([('sale_id','=',order.id)])
                    #if len(stock_picking_ids) > 0:
                    for stock in stock_picking_ids:
                        invoice_line = self.env['account.invoice.line'].sudo().search([('stock_picking_id','=',stock.id)])
                        exist_account_invoice = False
                        if invoice_line:
                            exist_account_invoice = True
                            account_invoice = self.env['account.invoice'].sudo().search([('id','=',invoice_line[0].invoice_id.id)])
                        #N° Embarque
                        sheet.write(row, col, stock.shipping_number if stock.shipping_number else '') 
                        col += 1
                        #Fecha de Zarpe
                        sheet.write(row, col, stock.departure_date.strftime("%d-%m-%Y") if stock.departure_date else '')
                        col += 1
                        #Semana ETD
                        sheet.write(row, col, stock.etd_week)
                        col += 1
                        #Cargar Hasta
                        sheet.write(row, col, stock.required_loading_date.strftime("%d-%m-%Y") if stock.required_loading_date else '')
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
                        sheet.write(row, col, order.contract_number if order.contract_number else '')
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
                        spanish_state = ''
                        if stock.state == 'draft':
                            spanish_state = 'Borrador'
                        elif stock.state == 'assigned':
                            spanish_state = 'Asignado'
                        elif stock.state == 'confirmed':
                            spanish_state = 'Confirmado'
                        elif stock.state == 'done':
                            spanish_state = 'Realizado'
                        else:
                            spanish_state = 'Cancelado'
                        
                        sheet.write(row, col, spanish_state)
                        col += 1
                        #Estatus Calidad
                        sheet.write(row, col, "pendiente")
                        col += 1
                        #Fecha Envio al Cliente
                        sheet.write(row, col, "pendiente")
                        col += 1

                        product_set = ''
                        price_set = ''
                        species = []
                        varieties = []
                        colors = []
                        calibers = []
                        brands = []
                        cannings = []
                        
                        for line in order.order_line:
                            for item in invoice_line:
                                if line.product_id.id == item.product_id.id:
                                    price_set += str(item.price_unit) + ' '
                            product_set += line.product_id.name + ' '
                            for attribute in line.product_id.attribute_value_ids:
                                if attribute.attribute_id.name == 'Variedad':
                                    if attribute.name not in varieties:
                                        varieties.append(attribute.name)
                                if attribute.attribute_id.name == 'Marca':
                                    if attribute.name not in brands:
                                        brands.append(attribute.name)
                                if attribute.attribute_id.name == 'Tipo de envase':
                                    if attribute.name not in cannings:
                                        cannings.append(attribute.name)
                                if attribute.attribute_id.name == 'Calibre':
                                    if attribute.name not in calibers:
                                        calibers.append(attribute.name)
                                if attribute.attribute_id.name == 'Especie':
                                    if attribute.name not in species:
                                        species.append(attribute.name)

                        #Especie
                        sheet.write(row, col, ' '.join([s for s in species]))
                        col += 1
                        #Variedad
                        sheet.write(row, col, ' '.join([v for v in varieties]))
                        col += 1
                        #Color
                        sheet.write(row, col, ' '.join([c for c in colors]))
                        col += 1
                        #Producto
                        sheet.write(row, col, product_set)
                        col += 1
                        #Calibre
                        sheet.write(row, col, ' '.join([ca for ca in calibers]))
                        col += 1
                        #Kilos
                        sheet.write(row, col, "pendiente")
                        col += 1
                        #Precio
                        sheet.write(row, col, price_set)
                        col += 1
                        #Monto
                        if exist_account_invoice:
                            sheet.write(row, col, account_invoice.amount_total if account_invoice.amount_total else '')
                        else:
                            sheet.write(row, col, "")
                        col += 1
                        #N° Factura
                        if exist_account_invoice:
                            sheet.write(row, col, account_invoice.dte_folio if account_invoice.dte_folio else '')
                        else:
                            sheet.write(row, col, "")
                        col += 1
                        #Cláusula
                        if exist_account_invoice:
                            sheet.write(row, col, account_invoice.export_clause.name if account_invoice.export_clause else '')
                        else:
                            sheet.write(row, col, "")
                        col += 1
                        #Envase
                        sheet.write(row, col, ' '.join([e for e in cannings]))
                        col += 1
                        #Modo de carga
                        if exist_account_invoice:
                            sheet.write(row, col,  account_invoice.charging_mode if  account_invoice.charging_mode else '')
                        else:
                            sheet.write(row, col, "")
                        col += 1
                        #Etiqueta Cliente
                        sheet.write(row, col, "pendiente")
                        col += 1
                        #Marca
                        sheet.write(row, col, ' '.join([b for b in brands]))
                        col += 1
                        #Agente
                        sheet.write(row, col, stock.agent_id.name if stock.agent_id else '')
                        col += 1
                        #Comisión
                        sheet.write(row, col, f'{stock.commission}%' if stock.commission else '')
                        col += 1
                        #Valor Comisión
                        sheet.write(row, col, stock.total_commission if stock.total_commission else '')  
                        col += 1
                        #Puerto de Carga
                        sheet.write(row, col, stock.departure_port.name if stock.departure_port else '')
                        col += 1
                        #Puerto de Destino
                        sheet.write(row, col, stock.arrival_port.name if stock.arrival_port else '')
                        col += 1
                        #Destino Final
                        if exist_account_invoice:
                            sheet.write(row, col, account_invoice.city_final_destiny_id.city_country if account_invoice.city_final_destiny_id.city_country else '')
                        else:
                            sheet.write(row, col, "")
                        col += 1
                        #Vía de Transporte
                        sheet.write(row, col, stock.type_transport.name if stock.type_transport else '')
                        col += 1
                        #Planta de Carga
                        if exist_account_invoice:
                            sheet.write(row, col, account_invoice.plant.name if account_invoice.plant else '')
                        else:
                            sheet.write(row, col, "")
                        col += 1
                        #Fecha y Hora de Carga
                        sheet.write(row, col, stock.required_loading_date if stock.required_loading_date else '',)
                        col += 1
                        #N° de Guía
                        sheet.write(row, col, stock.dte_folio if stock.dte_folio else '')
                        col += 1
                        #Nave / Viaje
                        sheet.write(row, col, stock.ship.name if stock.ship else '')
                        col += 1
                        #Naviera
                        sheet.write(row, col, stock.shipping_company.name if stock.shipping_company else '')  
                        col += 1
                        #N° Booking
                        sheet.write(row, col, stock.booking_number if stock.booking_number else '')
                        col += 1
                        #N° BL
                        if stock.bl_number:
                            sheet.write(row, col, stock.bl_number)
                            total_bl += 1
                        else:
                            sheet.write(row, col, "")
                        col += 1
                        #Stacking
                        if exist_account_invoice:
                            sheet.write(row, col, account_invoice.stacking if account_invoice.stacking else '')
                        else:
                            sheet.write(row, col, "")
                        col += 1
                        #Cut Off Document
                        if exist_account_invoice:
                            sheet.write(row, col, account_invoice.cut_off if account_invoice.cut_off else '')
                        else:
                            sheet.write(row, col, "")
                        col += 1
                        #Fecha Real de Zarpe
                        sheet.write(row, col, stock.departure_date.strftime("%d-%m-%Y") if stock.departure_date else '')
                        col += 1
                        #Fecha Real Arribo
                        sheet.write(row, col, stock.arrival_date.strftime("%d-%m-%Y") if stock.arrival_date else '')
                        col += 1
                        #N° Container
                        if stock.container_number:
                            sheet.write(row, col, stock.container_number)
                            total_container += 1
                        else:
                            sheet.write(row, col, '')
                        col += 1
                        #Tipo Container
                        sheet.write(row, col, stock.container_type.name if stock.container_type else '')
                        col += 1
                        #Terminal Portuario Origen
                        sheet.write(row, col, "pendiente")
                        col += 1
                        #Depósito Retiro
                        if exist_account_invoice:
                            sheet.write(row, col, account_invoice.withdrawal_deposit.name if account_invoice.withdrawal_deposit else '')
                        else:
                            sheet.write(row, col, "")
                        col += 1
                        #Valor Flete
                        sheet.write(row, col, stock.freight_value if stock.freight_value else '')
                        col +=1
                        #Valor Seguro
                        sheet.write(row, col, stock.safe_value if stock.safe_value else '')
                        col += 1
                        #FOB total
                        if exist_account_invoice:
                            sheet.write(row, col, account_invoice.total_value if account_invoice.total_value != 0 else '')
                        else:
                            sheet.write(row, col, "")
                        col += 1
                        #FOB / Kg
                        if exist_account_invoice:
                            sheet.write(row, col, account_invoice.value_per_kilogram if account_invoice.value_per_kilogram != 0 else '')
                        else:
                            sheet.write(row, col, "")
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

            #Total    
            row += 1
            sheet.set_row(row, cell_format=formats['title'])
            sheet.write(row, 0, "Total", formats['title'])
            sheet.write(row, 19, "Total Kg", formats['title'])
            sheet.write(row, 21, "Total Monto", formats['title'])
            sheet.write(row, 31, "Total Comisión", formats['title'])
            sheet.write(row, 42, f'Total BL= {total_bl}', formats['title'])
            sheet.write(row, 47, f'Total Container= {total_container}', formats['title'])
            sheet.write(row, 51, "Total Flete", formats['title'])
            sheet.write(row, 52, "Total Seguro", formats['title'])
            sheet.write(row, 53, "Total FOB", formats['title'])
            sheet.write(row, 54, "Total FOB por Kilo", formats['title'])

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
            'bold': 1,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color':'#8064a2',
            'font_color': 'white',
            'text_wrap': True
        })
        merge_format_total = workbook.add_format({
            'border': 1,
            'bold': 1,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '#,##0'
        })
        merge_format_total_text = workbook.add_format({
            'border': 1,
            'bold': 1,
            'align': 'left',
            'valign': 'vcenter'
        })
        return {
            'string': merge_format_string,
            'number': merge_format_number,
            'title': merge_format_title,
            'total': merge_format_total,
            'text_total': merge_format_total_text
        }