
import base64
from datetime import date
import string
import xlsxwriter
from odoo import fields, models, api
from collections import Counter
import logging
_logger = logging.getLogger('TEST report =======')

class AccountInvoiceXlsx(models.Model):
    _name = 'account.invoice.xlsx'

    purchase_file = fields.Binary(
        "Libro de Compra")

    company_get_id = fields.Many2one('res.company', 'Compañia')

    purchase_report_name = fields.Char("Reporte Compra",
                                       )

    sale_file = fields.Binary(
        "Libro de Venta")

    sale_report_name = fields.Char("Reporte Venta")

    from_date = fields.Date('Desde')

    to_date = fields.Date('Hasta')

    both = fields.Boolean("Ambas")
    book_type  = fields.Selection([('sale', 'Ventas'), ('purchase', 'Compra'), ('employee_fee', 'Honorarios')], default='sale', string='Tipo de Libro')

    def generate_honorarios_book_pdf(self):
        self.ensure_one()
        [data] = self.read()
        data['move_ids'] = self.env.context.get('active_ids', [])
        invoices = self.env['account.invoice'].browse(data['move_ids'])
        datas = {
            'ids': [],
            'model': 'account.invoice',
            'form': data
        }
        return self.env.ref('dimabe_billing_rut.honorarios_book_pdf_report').report_action(invoices, data=datas)

    def generate_purchase_book_pdf(self):
        self.ensure_one()
        [data] = self.read()
        data['move_ids'] = self.env.context.get('active_ids', [])
        invoices = self.env['account.invoice'].browse(data['move_ids'])
        datas = {
            'ids': [],
            'model': 'account.invoice',
            'form': data
        }
        return self.env.ref('dimabe_billing_rut.purchase_book_pdf_report').report_action(invoices, data=datas)
    
    def generate_sale_book_pdf(self):
        self.ensure_one()
        [data] = self.read()
        data['move_ids'] = self.env.context.get('active_ids', [])
        invoices = self.env['account.invoice'].browse(data['move_ids'])
        datas = {
            'ids': [],
            'model': 'account.invoice',
            'form': data
        }
        return self.env.ref('dimabe_billing_rut.sale_book_pdf_report').report_action(invoices, data=datas)
    
    @api.multi
    def generate_honorarios_book(self):
        file_name = 'honorarios.xlsx'
        workbook = xlsxwriter.Workbook(file_name, {'in_memory': True, 'strings_to_numbers': True})
        formats = self.set_formats(workbook)
        count_invoice = 0
        srow = 0
        for item in self:
            array_worksheet = []
            companies = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
            company_name = ''
            begin = 0
            end = 0
            
            for com in companies:
                worksheet = workbook.add_worksheet(com.display_name)
                array_worksheet.append({
                    'company_object': com, 'worksheet': worksheet
                })
            for wk in array_worksheet:
                sheet = wk['worksheet']
                region = self.env['region.address'].search([('id', '=', 1)])
                titles = ['Cod.SII', 'Folio', 'Cor.Interno', 'Fecha', 'RUT', 'Nombre', '#', 'NETO', 'IMPTO (11.5%)']
                invoices_get_tax = self.env['account.invoice'].sudo().search(
                    [('dte_type_id', '!=', None), ('company_id', '=', self.company_get_id.id),
                     ('date', '>=', self.from_date), ('date', '<=', self.to_date)])
                taxes_title = list(
                    dict.fromkeys(invoices_get_tax.mapped('tax_line_ids').mapped('tax_id').mapped('name')))

                titles.append('Total')
                sheet.merge_range(0, 0, 0, 2, self.company_get_id.display_name, formats['title'])
                sheet.merge_range(1, 0, 1, 2, self.company_get_id.invoice_rut, formats['title'])
                sheet.merge_range(2, 0, 2, 2,
                                  f'{self.company_get_id.city},Region {self.company_get_id.region_address_id.name}',
                                  formats['title'])
                sheet.merge_range(4, 3, 4, 6, 'Libro de Honorarios', formats['title'])
                sheet.merge_range(5, 3, 5, 6, 'Libro de Honorarios Ordenado por fecha', formats['title'])
                sheet.write(6, 8, 'Fecha', formats['title'])
                sheet.write(6, 9, date.today().strftime('%Y-%m-%d'), formats['title'])
                sheet.merge_range(6, 3, 6, 6, f'Desde {self.from_date} Hasta {self.to_date}', formats['title'])
                sheet.merge_range(7, 3, 7, 6, 'Moneda : Peso Chileno', formats['title'])
                row = 10
                col = 0
                
                for title in titles:
                    sheet.write(row, col, title, formats['title'])
                    col += 1
                row += 2
                col = 0
                sheet.merge_range(row, col, row, 5, 'Boleta electrónica. (BOLETA ELECTRONICA)',
                                  formats['title'])
                row += 1
                domain_invoices = [('date', '>=', self.from_date),
                     ('type', 'in', ('in_invoice', 'in_refund')),
                     ('date', '<=', self.to_date), ('dte_type_id.code', '=', 39),
                     ('journal_id.employee_fee', '=', True),
                     ('company_id.id', '=', self.company_get_id.id)]
                #cambio en Order
                invoices = self.env['account.invoice'].sudo().search(domain_invoices, order='date asc, reference asc') #facturas electronicas
                begin = row
                row += 1
                data_invoice = self.set_data_for_excel(sheet, row, invoices, taxes_title, titles, formats, exempt=False, employee_fee=True)
                #OKKKKK
                invoice_total = data_invoice.get('total').get('total')
                invoice_net = data_invoice.get('total').get('net')
                invoice_tax = data_invoice.get('total').get('tax')
                sheet = data_invoice['sheet']
                row = data_invoice['row']
                count_invoice += data_invoice['count_invoice']
                
                net_total = invoice_net 
                tax_total = invoice_tax
                total_total = invoice_total
                net_tax_total = net_total
                sheet.write(row + 3, col + 5, 'Total General', formats['title'])
                sheet.write(row + 3, col + 6, count_invoice, formats['total']) #SUMA DOCUMENTOS
                # sheet.write(row + 3, col + 7, exempt_total, formats['total'])
                # sheet.write(row + 3, col + 8, net_tax_total, formats['total'])
                sheet.write(row + 3, col + 7, net_total, formats['total'])
                sheet.write(row + 3, col + 8, tax_total, formats['total'])
                # sheet.write(row + 3, col + 11, 0, formats['total']) #TODO totoales iva no recuperable
                sheet.write(row + 3, col + 9, total_total, formats['total'])

        workbook.close()
        with open(file_name, "rb") as file:
            file_base64 = base64.b64encode(file.read())
        file_name = 'Libro de Honorarios {} {}.xlsx'.format(company_name, date.today().strftime("%d/%m/%Y"))
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

       

    @api.multi
    def generate_purchase_book(self):
        file_name = 'salebook.xlsx'
        workbook = xlsxwriter.Workbook(file_name, {'in_memory': True, 'strings_to_numbers': True})
        formats = self.set_formats(workbook)
        count_invoice = 0
        srow = 0
        for item in self:
            array_worksheet = []
            companies = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
            company_name = ''
            begin = 0
            end = 0
            
            for com in companies:
                worksheet = workbook.add_worksheet(com.display_name)
                array_worksheet.append({
                    'company_object': com, 'worksheet': worksheet
                })
            for wk in array_worksheet:
                sheet = wk['worksheet']
                region = self.env['region.address'].search([('id', '=', 1)])
                titles = ['Cod.SII', 'Folio', 'Cor.Interno', 'Fecha', 'RUT', 'Nombre', '#', 'EXENTO', 'NETO IVA', 'TOTAL NETO', 'IVA',
                          'IVA NO RECUPERABLE']
                invoices_get_tax = self.env['account.invoice'].sudo().search(
                    [('dte_type_id', '!=', None), ('company_id', '=', self.company_get_id.id),
                     ('date', '>=', self.from_date), ('date', '<=', self.to_date)])
                taxes_title = list(
                    dict.fromkeys(invoices_get_tax.mapped('tax_line_ids').mapped('tax_id').mapped('name')))
                # for tax in taxes_title:
                #     if tax != 'IVA Crédito' and tax != 'IVA Débito' and tax != 'Exento':
                #         titles.append(tax.upper())

                titles.append('Total')
                sheet.merge_range(0, 0, 0, 2, self.company_get_id.display_name, formats['title'])
                sheet.merge_range(1, 0, 1, 2, self.company_get_id.invoice_rut, formats['title'])
                sheet.merge_range(2, 0, 2, 2,
                                  f'{self.company_get_id.city},Region {self.company_get_id.region_address_id.name}',
                                  formats['title'])
                sheet.merge_range(4, 3, 4, 6, 'Libro de Compras', formats['title'])
                sheet.merge_range(5, 3, 5, 6, 'Libro de Compras Ordenado por fecha', formats['title'])
                sheet.write(6, 10, 'Fecha', formats['title'])
                sheet.write(6, 11, date.today().strftime('%Y-%m-%d'), formats['title'])
                sheet.merge_range(6, 3, 6, 6, f'Desde {self.from_date} Hasta {self.to_date}', formats['title'])
                sheet.merge_range(7, 3, 7, 6, 'Moneda : Peso Chileno', formats['title'])
                row = 12
                col = 0
                
                for title in titles:
                    sheet.write(row, col, title, formats['title'])
                    col += 1
                row += 2
                col = 0
                sheet.merge_range(row, col, row, 5, 'Factura de compra electronica. (FACTURA COMPRA ELECTRONICA)',
                                  formats['title'])
                row += 1
                domain_invoices = [('date', '>=', self.from_date),
                     ('type', 'in', ('in_invoice', 'in_refund')),
                     ('date', '<=', self.to_date), ('dte_type_id.code', '=', 33),
                     ('company_id.id', '=', self.company_get_id.id)]
                #cambio en Order
                invoices = self.env['account.invoice'].sudo().search(domain_invoices, order='date asc, reference asc') #facturas electronicas
                begin = row
                row += 1
                data_invoice = self.set_data_for_excel(sheet, row, invoices, taxes_title, titles, formats, exempt=False)
                invoice_total = data_invoice.get('total').get('total')
                invoice_net = data_invoice.get('total').get('net')
                invoice_tax = data_invoice.get('total').get('tax')
                sheet = data_invoice['sheet']
                row = data_invoice['row']
                count_invoice += data_invoice['count_invoice']

                exempts = self.env['account.invoice'].sudo().search([('date', '>=', self.from_date),
                                                                     ('type', 'in', ('in_invoice', 'in_refund')),
                                                                     ('date', '<=', self.to_date),
                                                                     ('dte_type_id.code', '=', 34),
                                                                     ('company_id.id', '=', self.company_get_id.id)],
                                                                     order='date asc, reference asc')  #ORDENA ASCENDENTE
                row += 2
                sheet.merge_range(row, col, row, 5,
                                  'Factura de compra exenta electronica. (FACTURA COMPRA ELECTRONICA)',
                                  formats['title'])
                row += 1
                data_exempt = self.set_data_for_excel(sheet, row, exempts, taxes_title, titles, formats, exempt=True)
                exempt_total = data_exempt.get('total').get('total')
                exempt_net = data_exempt.get('total').get('net')
                exempt_tax = data_exempt.get('total').get('tax')
                sheet = data_exempt['sheet']
                row = data_exempt['row']
                count_invoice += data_exempt['count_invoice']                
                
                credit = self.env['account.invoice'].sudo().search([('date', '>=', self.from_date),
                                                                    ('type', 'in', ('in_invoice', 'in_refund')),
                                                                    ('date', '<=', self.to_date),
                                                                    ('dte_type_id.code', '=', 61),
                                                                    ('company_id.id', '=', self.company_get_id.id)],
                                                                    order='date asc, reference asc') #ORDENA ASCENDENTE

                row += 2
                sheet.merge_range(row, col, row, 5,
                                  'NOTA DE CREDITO COMPRA ELECTRONICA (NOTA DE CREDITO COMPRA ELECTRONICA)',
                                  formats['title'])
                row += 1
                data_credit = self.set_data_for_excel(sheet, row, credit, taxes_title, titles, formats, exempt=False)
                credit_total = data_credit.get('total').get('total')
                credit_net = data_credit.get('total').get('net')
                credit_tax = data_credit.get('total').get('tax')
                sheet = data_credit['sheet']
                row = data_credit['row']
                count_invoice += data_credit['count_invoice']
                row += 2
                sheet.merge_range(row, col, row, 5,
                                  'NOTA DE DEBITO COMPRA ELECTRONICA (NOTA DE DEBITO COMPRA ELECTRONICA)',
                                  formats['title'])
                row += 1

                debit = self.env['account.invoice'].sudo().search([('date', '>=', self.from_date),
                                                                   ('date', '<=', self.to_date),
                                                                   ('type', 'in', ('in_invoice', 'in_refund')),
                                                                   ('dte_type_id.code', '=', 56),
                                                                   ('company_id.id', '=', self.company_get_id.id)],
                                                                   order='date asc, reference asc') #ORDENA ASCENDENTE
                                                                   
                data_debit = self.set_data_for_excel(sheet, row, debit, taxes_title, titles, formats, exempt=False)
                debit_total = data_debit.get('total').get('total')
                debit_net = data_debit.get('total').get('net')
                debit_tax = data_debit.get('total').get('tax')
                sheet = data_debit['sheet']
                row = data_debit['row'] 
                count_invoice += data_debit['count_invoice']
                
                net_total = invoice_net + exempt_net - abs(credit_net) + abs(debit_net)
                tax_total = invoice_tax + exempt_tax - abs(credit_tax) + abs(debit_tax)
                total_total = invoice_total + exempt_total - abs(credit_total) + abs(debit_total)
                net_tax_total = net_total - exempt_net
                sheet.write(row + 3, col + 5, 'Total General', formats['title'])
                sheet.write(row + 3, col + 6, count_invoice, formats['total']) #SUMA DOCUMENTOS
                sheet.write(row + 3, col + 7, exempt_total, formats['total'])
                sheet.write(row + 3, col + 8, net_tax_total, formats['total'])
                sheet.write(row + 3, col + 9, net_total, formats['total'])
                sheet.write(row + 3, col + 10, tax_total, formats['total'])
                sheet.write(row + 3, col + 11, 0, formats['total']) #TODO totoales iva no recuperable
                sheet.write(row + 3, col + 12, total_total, formats['total'])

        workbook.close()
        with open(file_name, "rb") as file:
            file_base64 = base64.b64encode(file.read())
        file_name = 'Libro de Compras {} {}.xlsx'.format(company_name, date.today().strftime("%d/%m/%Y"))
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

    @api.multi
    def generate_sale_book(self):
        count_invoice = 0
        for item in self:
            file_name = 'salebook.xlsx'
            array_worksheet = []
            companies = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
            workbook = xlsxwriter.Workbook(file_name, {'in_memory': True, 'strings_to_numbers': True})
            company_name = ''
            begin = 0
            end = 0
            
            for com in companies:
                worksheet = workbook.add_worksheet(com.display_name)
                array_worksheet.append({
                    'company_object': com, 'worksheet': worksheet
                })
            for wk in array_worksheet:
                sheet = wk['worksheet']
                formats = self.set_formats(workbook)
                region = self.env['region.address'].search([('id', '=', 1)])
                titles = ['Cod.SII', 'Folio', 'Cor.Interno', 'Fecha', 'RUT', 'Nombre', '#', 'EXENTO', 'NETO IVA', 'NETO', 'IVA',
                          'IVA NO RECUPERABLE']
                invoices_get_tax = self.env['account.invoice'].sudo().search(
                    [('dte_type_id', '!=', None), ('company_id', '=', self.company_get_id.id)])
                taxes_title = list(
                    dict.fromkeys(invoices_get_tax.mapped('tax_line_ids').mapped('tax_id').mapped('name')))
                # for tax in taxes_title:
                #     if tax != 'IVA Crédito' and tax != 'IVA Débito' and tax != 'Exento':
                #         titles.append(tax.upper())

                titles.append('Total')
                sheet.merge_range(0, 0, 0, 2, self.company_get_id.display_name, formats['title'])
                sheet.merge_range(1, 0, 1, 2, self.company_get_id.invoice_rut, formats['title'])
                sheet.merge_range(2, 0, 2, 2,
                                  f'{self.company_get_id.city},Region {self.company_get_id.region_address_id.name}',
                                  formats['title'])
                sheet.merge_range(4, 3, 4, 6, 'Libro de Ventas', formats['title'])
                sheet.merge_range(5, 3, 5, 6, 'Libro de Ventas Ordenado por fecha', formats['title'])
                sheet.write(6, 10, 'Fecha', formats['title'])
                sheet.write(6, 11, date.today().strftime('%Y-%m-%d'), formats['title'])
                sheet.merge_range(6, 3, 6, 6, f'Desde {self.from_date} Hasta {self.to_date}', formats['title'])
                sheet.merge_range(7, 3, 7, 6, 'Moneda : Peso Chileno', formats['title'])
                row = 12
                col = 0
                
                for title in titles:
                    sheet.write(row, col, title, formats['title'])
                    col += 1
                row += 2
                col = 0
                sheet.merge_range(row, col, row, 5, 'Factura de Ventas electronica. (FACTURA VENTAS ELECTRONICA)',
                                  formats['title'])
                row += 1
                invoices = self.env['account.invoice'].sudo().search(
                    [('date', '>=', self.from_date),
                     ('type', 'in', ('out_invoice', 'out_refund')),
                     ('date', '<=', self.to_date), ('dte_type_id.code', '=', 33),
                     ('company_id.id', '=', self.company_get_id.id)],
                     order='date asc, reference asc') #ORDEN ASCENDENTE 
                begin = row
                row += 1
                data_invoice = self.set_data_for_excel(sheet, row, invoices, taxes_title, titles, formats, exempt=False)
                invoice_total = data_invoice.get('total').get('total')
                invoice_net = data_invoice.get('total').get('net')
                invoice_tax = data_invoice.get('total').get('tax')
                sheet = data_invoice['sheet']
                row = data_invoice['row']
                count_invoice += data_invoice['count_invoice']
                exempts = self.env['account.invoice'].sudo().search([('date', '>=', self.from_date),
                                                                     ('type', 'in', ('out_invoice', 'out_refund')),
                                                                     ('date', '<=', self.to_date),
                                                                     ('dte_type_id.code', '=', 34),
                                                                     ('company_id.id', '=', self.company_get_id.id)],
                                                                     order='date asc, reference asc') #ORDEN ASCENDENTE
                row += 2
                sheet.merge_range(row, col, row, 5,
                                  'Factura de Ventas exenta electronica. (FACTURA VENTAS EXENTA ELECTRONICA)',
                                  formats['title'])
                row += 1
                data_exempt = self.set_data_for_excel(sheet, row, exempts, taxes_title, titles, formats, exempt=True)
                exempt_total = data_exempt.get('total').get('total')
                exempt_net = data_exempt.get('total').get('net')
                exempt_tax = data_exempt.get('total').get('tax')
                sheet = data_exempt['sheet']
                row = data_exempt['row'] 
                count_invoice += data_exempt['count_invoice']              
                domain_credit = [
                    ('date', '>=', self.from_date),
                    ('date', '<=', self.to_date),
                    ('type', 'in', ('out_invoice', 'out_refund')),
                    ('dte_type_id.code', '=', 61), #TODO llevarlo a FE sii_document_type_id.code
                    ('company_id.id', '=', self.company_get_id.id)
                    ]
                credit = self.env['account.invoice'].sudo().search(domain_credit, order='date asc, reference asc')  # Ordena NOTAS DE CREDITO ASCENDENTES
                # _logger.info('LOG: ***** notas de credito {} domain {}'.format(credit, domain_credit))

                row += 2
                
                sheet.merge_range(row, col, row, 5,
                                  'Nota de Credito Ventas Electronica (NOTA DE CREDITO VENTAS ELECTRONICA)',
                                  formats['title'])
                row += 1
                data_credit = self.set_data_for_excel(sheet, row, credit, taxes_title, titles, formats, exempt=False)
                credit_total = data_credit.get('total').get('total')
                credit_net = data_credit.get('total').get('net')
                credit_tax = data_credit.get('total').get('tax')
                sheet = data_credit['sheet']
                row = data_credit['row']
                row += 2
                count_invoice += data_credit['count_invoice']

                sheet.merge_range(row, col, row, 5,
                                  'Nota de Debitos Ventas ELECTRONICA (NOTA DE DEBITO VENTAS ELECTRONICA)',
                                  formats['title'])
                row += 1
               

                debit = self.env['account.invoice'].sudo().search([('date', '>=', self.from_date),
                                                                   ('date', '<=', self.to_date),
                                                                   ('type', 'in', ('out_invoice', 'out_refund')),
                                                                   ('dte_type_id.code', '=', 56),
                                                                   ('company_id.id', '=', self.company_get_id.id)],
                                                                   order='date asc, reference asc') #ORDENA DEBITO ASCENDENTE
                data_debit = self.set_data_for_excel(sheet, row, debit, taxes_title, titles, formats, exempt=False)
                debit_total = data_debit.get('total').get('total')
                debit_net = data_debit.get('total').get('net')
                debit_tax = data_debit.get('total').get('tax')
                               
                sheet = data_debit['sheet']
                row = data_debit['row']
                count_invoice += data_debit['count_invoice']           
                

                # sheet.merge_range(row, col + 8, row + 2, 7, 'Totales', formats['title'])
                net_total = invoice_net + exempt_net - abs(credit_net) + abs(debit_net)
                tax_total = invoice_tax + exempt_tax - abs(credit_tax) + abs(debit_tax)
                total_total = invoice_total + exempt_total - abs(credit_total) + abs(debit_total)
                net_tax_total = net_total - exempt_net
                sheet.write(row + 3, col + 5, 'Total General', formats['title']) #SE CORRE UNA CELDA HACIA IZQUIERDA
                sheet.write(row + 3, col + 6, count_invoice, formats['total']) #SUMA DOCUMENTOS
                sheet.write(row + 3, col + 7, exempt_total, formats['total'])
                sheet.write(row + 3, col + 8, net_tax_total, formats['total'])
                sheet.write(row + 3, col + 9, net_total, formats['total'])
                sheet.write(row + 3, col + 10, tax_total, formats['total'])
                sheet.write(row + 3, col + 11, 0, formats['total']) #TODO totoales iva no recuperable
                sheet.write(row + 3, col + 12, total_total, formats['total'])

        workbook.close()
        with open(file_name, "rb") as file:
            file_base64 = base64.b64encode(file.read())
        file_name = 'Libro de Ventas {} {}.xlsx'.format(company_name, date.today().strftime("%d/%m/%Y"))
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

    def set_data_for_excel(self, sheet, row, invoices, taxes_title, titles, formats, exempt, employee_fee=False):
        for inv in invoices:
            col = 0
            data = self.set_data_invoice(sheet, col, row, inv, invoices, taxes_title, titles, formats)
            sheet = data['sheet']
            row = data['row']
            col = data['col']
            if inv.id == invoices[-1].id:
                row += 2
            else:
                row += 1
        sheet.merge_range(row, 0, row, 5, 'Totales:', formats['text_total'])
        col = 6
        count_invoice = len(invoices)
        sheet.write(row, col, count_invoice, formats['total']) ## Cantidad Total de Documentos
        col += 1
        exempt_sum = 0
        if employee_fee:
            sheet.write(row, col, sum(invoices.mapped('amount_untaxed')), formats['total']) ## Total neto 
            col += 1
            tax = sum(invoices.mapped('amount_tax'))
            sheet.write(row, col, tax, formats['total']) ## Total imptos
            col += 1
            sheet.write(row, col, abs(sum(invoices.mapped('amount_total'))), formats['total'])

            # sheet.write(row, col, sum(
            #     invoices.mapped('tax_line_ids').filtered(lambda a: 'IVA' in a.tax_id.name).mapped('amount')),
            #             formats['total'])
            # col += 1
            # sheet.write(row, col, 0, formats['total'])
            # col += 1
            # for tax in taxes_title:
            #     if tax in titles or str.upper(tax) in titles and 'Exento' not in tax:
            #         line = invoices.mapped('tax_line_ids').filtered(
            #             lambda a: str.lower(a.tax_id.name) == str.lower(tax) or str.upper(
            #                 a.tax_id.name) == tax).mapped(
            #             'amount')
            #         sheet.write(row, col, sum(line), formats['total'])
            #         col += 1
            # sheet.write(row, col, abs(sum(invoices.mapped('amount_total'))), formats['total'])
        else:
            exempt_sum = sum(invoices.mapped('invoice_line_ids').filtered(
            lambda a: 'Exento' in a.invoice_line_tax_ids.mapped('name') or len(
                a.invoice_line_tax_ids) == 0).mapped('price_subtotal'))
            sheet.write(row, col, exempt_sum, formats['total']) ## Total exento
            col += 1
            net_tax = sum(invoices.mapped('amount_untaxed')) - abs(exempt_sum)
            sheet.write(row, col, net_tax, formats['total']) ## Total exento
            col += 1
            sheet.write(row, col, sum(invoices.mapped('amount_untaxed')), formats['total'])
            # if exempt:
            #     sheet.write(row, col, sum(invoices.mapped('amount_untaxed_signed')), formats['total'])
            # else:
            #     sheet.write(row, col, sum(invoices.mapped('amount_untaxed_signed')), formats['total'])
            col += 1
            sheet.write(row, col, sum(
                invoices.mapped('tax_line_ids').filtered(lambda a: 'IVA' in a.tax_id.name).mapped('amount')),
                        formats['total'])
            col += 1
            sheet.write(row, col, 0, formats['total'])
            col += 1
            for tax in taxes_title:
                if tax in titles or str.upper(tax) in titles and 'Exento' not in tax:
                    line = invoices.mapped('tax_line_ids').filtered(
                        lambda a: str.lower(a.tax_id.name) == str.lower(tax) or str.upper(
                            a.tax_id.name) == tax).mapped(
                        'amount')
                    sheet.write(row, col, sum(line), formats['total'])
                    col += 1
            sheet.write(row, col, abs(sum(invoices.mapped('amount_total'))), formats['total'])
        col = 0
        return {
            'sheet': sheet, 
            'row': row, 
            'total': {
                'total' : sum(invoices.mapped('amount_total')),
                'net' : sum(invoices.mapped('amount_untaxed')),
                'tax': sum(invoices.mapped('amount_tax')),
                'exempt': exempt_sum,
            },
            'count_invoice': count_invoice
        }

    def set_data_invoice(self, sheet, col, row, inv, invoices, taxes_title, titles, formats):
        # _logger.info('LOG: -- fact %r neto %r iva %r', inv, inv.amount_untaxed, inv.amount_tax)
        sheet.write(row, col, inv.dte_type_id.code, formats['string'])
        col += 1
        # if inv.dte_folio:
        #     sheet.write(row, col, inv.dte_folio, formats['string'])
        #TODO esto es lo que debiera ir
        # if inv.sii_document_number:
        #     sheet.write(row, col, inv.sii_document_number, formats['string'])
        if inv.reference:
            sheet.write(row, col, inv.reference, formats['string'])
        col += 1
        if inv.number:
            sheet.write(row, col, inv.number, formats['string'])
        col += 1
        if inv.date:
            sheet.write(row, col, inv.date.strftime('%Y-%m-%d'), formats['string'])
        col += 1
        if inv.partner_id.invoice_rut:
            sheet.write(row, col, inv.partner_id.invoice_rut, formats['string'])
        col += 1
        long_name = max(invoices.mapped('partner_id').mapped('display_name'), key=len)
        sheet.set_column(col, col, len(long_name))
        sheet.write(row, col, inv.partner_id.display_name, formats['string'])
        col += 2

        # exempt_taxes = inv.invoice_line_ids.filtered(lambda a: a.sii_code == 0 and a.amount == 0.0)
        # affect_taxes = inv.invoice_line_ids.filtered(lambda a: a.sii_code == 14)

        exempt_taxes = inv.invoice_line_ids.filtered(lambda a: 'Exento' in a.invoice_line_tax_ids.mapped('name'))

        affect_taxes = inv.invoice_line_ids.filtered(lambda a: 'IVA Débito' in a.invoice_line_tax_ids.mapped('name'))
        employee_fee_taxes = inv.invoice_line_ids.filtered(lambda a: 'Retención Boleta Honorarios' in a.invoice_line_tax_ids.mapped('name'))

        if exempt_taxes:
            _logger.info('LOG .>:::__ exento')
            sheet.write(row, col, sum(exempt_taxes.mapped('price_subtotal')), formats['number'])
            col += 1
            net = inv.amount_untaxed_signed
            net_tax = net - abs(sum(exempt_taxes.mapped('price_subtotal')))
            sheet.write(row, col, net_tax, formats['number'])
            col += 1
            
            if inv.dte_type_id.id:
                sheet.write(row, col, inv.amount_untaxed, formats['number'])
                col += 1 

                sheet.write(row, col, inv.amount_tax, formats['number'])
                col += 1
                sheet.write(row, col, '0', formats['number'])
                col += 1
                for tax in taxes_title:
                    if tax in titles or str.upper(tax) in titles and 'Exento' not in tax:
                        line = inv.tax_line_ids.filtered(
                            lambda a: str.lower(a.tax_id.name) == str.lower(tax) or str.upper(
                                a.tax_id.name) == tax).mapped(
                            'amount')
                        sheet.write(row, col, sum(line), formats['number'])
                        col += 1
                sheet.write(row, col, inv.amount_total_signed, formats['number'])
            else:
                sheet.write(row, col, sum(inv.invoice_line_ids.filtered(inv.invoice_line_ids.filtered(
                    lambda a: 'Exento' not in a.invoice_line_tax_ids.mapped('name') or len(
                        a.invoice_line_tax_ids) != 0)).mapped('price_subtotal')), formats['number'])
                col += 1
                sheet.write(row, col, sum(inv.tax_line_ids.filtered(lambda a: 'IVA' in a.tax_id.name).mapped('amount')),
                            formats['number'])
                col += 1

                sheet.write(row, col, '0', formats['number'])
                col += 1
                for tax in taxes_title:
                    if tax in titles or str.upper(tax) in titles and 'Exento' not in tax:
                        line = inv.tax_line_ids.filtered(
                            lambda a: str.lower(a.tax_id.name) == str.lower(tax) or str.upper(
                                a.tax_id.name) == tax).mapped(
                            'amount')
                        sheet.write(row, col, sum(line), formats['number'])
                        col += 1
                sheet.write(row, col, inv.amount_total_signed, formats['number'])
        elif affect_taxes:
            _logger.info('LOG .>:::__ afecto')
            sheet.write_number(row, col, 0, formats['number'])
            col += 1
            # sheet.write(row, col, inv.amount_untaxed_signed, formats['number'])
            net_tax = inv.amount_untaxed - abs(sum(exempt_taxes.mapped('price_subtotal')))
            sheet.write(row, col, net_tax, formats['number'])
            col += 1
            sheet.write(row, col, inv.amount_untaxed, formats['number']) ##Neto
            col += 1
            days = self.diff_dates(inv.date, date.today())
            if days <= 90:
                sheet.write(row, col,
                            sum(inv.tax_line_ids.filtered(lambda a: 'IVA' in a.tax_id.name).mapped('amount')),
                            formats['number'])
                col += 1
                sheet.write_number(row, col, 0, formats['number'])
                col += 1
            else:
                sheet.write_number(row, col, 0, formats['number'])
                col += 1
                # sheet.write(row, col, inv.amount_tax, formats['number'])
                sheet.write(row, col,
                            sum(inv.tax_line_ids.filtered(lambda a: 'IVA' in a.tax_id.name).mapped('amount')),
                            formats['number'])
                col += 1
            # for tax in taxes_title:
            #     if tax in titles or str.upper(tax) in titles and 'Exento' not in tax:
            #         line = inv.tax_line_ids.filtered(
            #             lambda a: str.lower(a.tax_id.name) == str.lower(tax) or str.upper(a.tax_id.name) == tax).mapped(
            #             'amount')
            #         sheet.write(row, col, sum(line), formats['number'])
            #         col += 1
            sheet.write(row, col, abs(inv.amount_total_signed), formats['number'])
        elif employee_fee_taxes:
            sheet.write_number(row, col, int(inv.amount_untaxed), formats['number'])
            col += 1
            # sheet.write(row, col, inv.amount_untaxed_signed, formats['number'])
            # net_tax = inv.amount_untaxed - abs(sum(exempt_taxes.mapped('price_subtotal')))
            sheet.write(row, col, int(inv.amount_tax), formats['number'])
            col += 1
            sheet.write(row, col, int(inv.amount_total_signed), formats['number']) ##Neto
            col += 1
            # days = self.diff_dates(inv.date, date.today())
            # if days <= 90:
            #     sheet.write(row, col,
            #                 sum(inv.tax_line_ids.filtered(lambda a: 'IVA' in a.tax_id.name).mapped('amount')),
            #                 formats['number'])
            #     col += 1
            #     sheet.write_number(row, col, 0, formats['number'])
            #     col += 1
            # else:
            #     sheet.write_number(row, col, 0, formats['number'])
            #     col += 1
            #     # sheet.write(row, col, inv.amount_tax, formats['number'])
            #     sheet.write(row, col,
            #                 sum(inv.tax_line_ids.filtered(lambda a: 'IVA' in a.tax_id.name).mapped('amount')),
            #                 formats['number'])
            #     col += 1
            # for tax in taxes_title:
            #     if tax in titles or str.upper(tax) in titles and 'Exento' not in tax:
            #         line = inv.tax_line_ids.filtered(
            #             lambda a: str.lower(a.tax_id.name) == str.lower(tax) or str.upper(a.tax_id.name) == tax).mapped(
            #             'amount')
            #         sheet.write(row, col, sum(line), formats['number'])
            #         col += 1
            # sheet.write(row, col, abs(inv.amount_total_signed), formats['number'])


        
        line_out = {'sheet': sheet, 'row': row, 'col': col}

        return line_out

    def diff_dates(self, date1, date2):
        return abs(date2 - date1).days

    def get_another_taxes(self, inv):
        another = []
        for line in inv.mapped('invoice_line_ids'):

            if line.invoice_line_tax_ids and len(line.invoice_line_tax_ids) > 0:
                for tax in line.invoice_line_tax_ids:
                    if tax.amount != 19 and tax.amount > 0:
                        another.append(line)
        return another

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

