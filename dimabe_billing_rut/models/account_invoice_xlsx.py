from odoo import fields, models, api
import base64
import csv
import datetime
import io
import logging
import time
from datetime import datetime, date
import xlsxwriter
from dateutil import relativedelta


class AccountInvoiceXlsx(models.Model):
    _name = 'account.invoice.xlsx'

    report_file = fields.Binary(
        "Libro de Compra", default=lambda self: self.env['account.invoice.xlsx'].search([])[-1].report_file)

    report_name = fields.Char("Reporte")

    from_date = fields.Date('Desde')

    to_date = fields.Date('Hasta')

    both = fields.Boolean("Ambas")

    @api.multi
    def generate_book(self):
        for item in self:
            file_name = 'temp'
            array_worksheet = []
            today = date.today()
            companies = self.env['res.company'].search(
                [('add_to_sale_book', '=', True)], order='id asc')
            workbook = xlsxwriter.Workbook(file_name, {'in_memory': True})
            for com in companies:
                worksheet = workbook.add_worksheet(com.display_name)
                array_worksheet.append(
                    {'company_name': com.display_name, 'company_id': com.id, 'worksheet': worksheet})
            for wk in array_worksheet:
                sheet = wk['worksheet']
                sheet = self.set_size(sheet)
                merge_format_string = workbook.add_format({
                    'border': 0,
                    'align': 'center',
                    'valign': 'vcenter',
                })
                merge_format_title = workbook.add_format({
                    'bold': 1,
                    'border': 1,
                    'align': 'center',
                    'valign': 'vcenter',
                })
                company = self.env['res.company'].search(
                    [('id', '=', wk['company_id'])])
                region = self.env['region.address'].search([('id', '=', 1)])
                sheet.merge_range(
                    'A1:C1', wk['company_name'], merge_format_string)
                sheet.merge_range('A2:C2', company.vat, merge_format_string)
                sheet.merge_range('A3:C3', '{}, Region {}'.format(
                    company.city, region.name.capitalize()), merge_format_string)
                sheet.merge_range('A5:L5', 'Libro de Compras',
                                  merge_format_title)
                sheet.merge_range(
                    'A6:L6', 'Libro de Compras Ordenado Por fecha	', merge_format_string)
                sheet.write('K7', 'Fecha:', merge_format_string)
                sheet.write('L7', today.strftime(
                    "%d-%m-%Y"), merge_format_string)

                sheet.merge_range('A8:L8', 'Desde : {} Hasta : {}'.format(self.from_date.strftime(
                    "%d/%m/%Y"), self.to_date.strftime("%d/%m/%Y")), merge_format_string)
                sheet.merge_range(
                    'A9:L9', 'Moneda : Peso Chileno', merge_format_string)
                sheet = self.set_title(sheet, merge_format_title)

                invoice = self.env['account.invoice'].search([('company_id.id','=',company.id),('type','=','in_invoice')])
                row = 12
                for inv in invoice:
                    sheet.write('C{}'.format(str(row)),inv.number,merge_format_string)
                    row += 1
            workbook.close()
            with open(file_name, "rb") as file:
                file_base64 = base64.b64encode(file.read())
            self.write({'report_file': file_base64,
                        'report_name': 'Libro de Ventas'})
            return {
                "type": "ir.actions.do_nothing",
            }

    def set_title(self, sheet, format):
        sheet.write('A11', 'Cod.SII', format)
        sheet.write('B11', 'Folio', format)
        sheet.write('C11', 'Cor.Interno', format)
        sheet.write('D11', 'Fecha', format)
        sheet.write('E11', 'RUT', format)
        sheet.write('F11', 'Nombre de Proevedor', format)
        sheet.write('H11', 'EXENTO', format)
        sheet.write('I11', 'NETO', format)
        sheet.write('J11', 'iIVA', format)
        sheet.write('K11', 'IVA NO RECUPERABLE', format)
        sheet.write('L11', 'Total', format)
        return sheet

    def set_size(self, sheet):
        sheet.set_column('F:F', 40)
        sheet.set_column('L:L', 20)
        sheet.set_column('A:A', 6)
        sheet.set_column('C:C', 10)
        sheet.set_column('G:G',3)
        sheet.set_row(9, 6)
        return sheet
