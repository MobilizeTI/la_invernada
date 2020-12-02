import base64
import csv
import datetime
import io
import logging
import time
from datetime import datetime, date

import xlsxwriter
from dateutil import relativedelta
from odoo import fields, models, api


class AccountInvoiceXlsx(models.Model):
    _name = 'account.invoice.xlsx'

    purchase_file = fields.Binary(
        "Libro de Compra", default=lambda self: self.env['account.invoice.xlsx'].search([])[-1].purchase_file)

    purchase_report_name = fields.Char("Reporte Compra",
                                       default=lambda self: self.env['account.invoice.xlsx'].search([])[
                                           -1].purchase_report_name)

    sale_file = fields.Binary(
        "Libro de Venta", default=lambda self: self.env['account.invoice.xlsx'].search([])[-1].sale_file)

    sale_report_name = fields.Char("Reporte Venta", default=lambda self: self.env['account.invoice.xlsx'].search([])[
        -1].sale_report_name)

    from_date = fields.Date('Desde')

    to_date = fields.Date('Hasta')

    both = fields.Boolean("Ambas")

    @api.multi
    def generate_sale_book(self):
        for item in self:
            file_name = 'temp'
            array_worksheet = []
            today = date.today()
            companies = self.env['res.company'].search(
                [('id', '=', self.env.user.company_id.id)], order='id asc')
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
                merge_format_number = workbook.add_format({
                    'bold': 0,
                    'align': 'center',
                    'valign': 'vcenter',
                    'num_format': '0,000'
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
                    'num_format': '0,000'
                })
                merge_format_total_text = workbook.add_format({
                    'border': 1,
                    'bold': 1,
                    'align': 'left',
                    'valign': 'vcenter'
                })
                company = self.env['res.company'].search(
                    [('id', '=', wk['company_id'])])
                region = self.env['region.address'].search([('id', '=', 1)])
                sheet.merge_range(
                    'A1:C1', wk['company_name'], merge_format_string)
                sheet.merge_range('A2:C2', company.vat, merge_format_string)
                sheet.merge_range('A3:C3', '{}, Region {}'.format(
                    company.city, region.name.capitalize()), merge_format_string)
                sheet.merge_range('A5:L5', 'Libro de Ventas',
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

                invoice = self.env['account.invoice'].search(
                    [('company_id.id', '=', company.id), ('type', '=', 'out_invoice'), ('state', '=', 'paid'),
                     ('date_invoice', '>', self.from_date), ('date_invoice', '<', self.to_date)])
                row = 14
                sheet.merge_range('A13:F13', 'Factura de compra electronica. (FACTURA COMPRA ELECTRONICA)',
                                  merge_format_total_text)
                for inv in invoice:
                    sheet.write('B{}'.format(str(row)), inv.reference, merge_format_string)
                    sheet.write('C{}'.format(str(row)), inv.number, merge_format_string)
                    sheet.write('D{}'.format(str(row)), inv.date_invoice.strftime("%d/%m/%Y"), merge_format_string)
                    rut = inv.partner_id.invoice_rut
                    if not rut:
                        rut = ''
                    sheet.write('E{}'.format(str(row)), rut, merge_format_string)
                    sheet.write('F{}'.format(str(row)), inv.partner_id.display_name, merge_format_string)
                    sheet.write('H{}'.format(str(row)), round(inv.amount_untaxed_invoice_signed), merge_format_number)
                    sheet.write('I{}'.format(str(row)), round(inv.amount_total_signed), merge_format_number)
                    days = self.diff_dates(inv.date_invoice, today)
                    if days > 90:
                        sheet.write('K{}'.format(str(row)), round(inv.amount_tax), merge_format_number)
                        sheet.write('J{}'.format(str(row)), '0', merge_format_number)
                    else:
                        sheet.write('K{}'.format(str(row)), '0', merge_format_number)
                        sheet.write('J{}'.format(str(row)), round(inv.amount_tax), merge_format_number)
                    sheet.write_formula('L{}'.format(str(row)), '=SUM(H{}:J{})'.format(str(row), str(row)),
                                        merge_format_number)
                    row += 1
                total = row + 1
                sheet.merge_range('A{}:F{}'.format((row + 1), (row + 1)),
                                  'Total Factura de compra electronica. (FACTURA COMPRA ELECTRONICA)',
                                  merge_format_total_text)
                sheet.write('G{}'.format(str(total)), str(len(invoice)), merge_format_total)
                sheet.write_formula('H{}'.format(str(total)), '=SUM(H{}:H{})'.format((row - len(invoice)), row),
                                    merge_format_total)
                sheet.write_formula('I{}'.format(str(total)), '=SUM(I{}:I{})'.format((row - len(invoice)), row),
                                    merge_format_total)
                sheet.write_formula('J{}'.format(str(total)), '=SUM(J{}:J{})'.format((row - len(invoice)), row),
                                    merge_format_total)
                sheet.write_formula('K{}'.format(str(total)), '=SUM(K{}:K{})'.format((row - len(invoice)), row),
                                    merge_format_total)
                sheet.write_formula('L{}'.format(str(total)), '=SUM(L{}:L{})'.format((row - len(invoice)), row),
                                    merge_format_total)
                invoice_refund = self.env['account.invoice'].search(
                    [('company_id.id', '=', company.id), ('type', '=', 'out_refund'), ('state', '=', 'paid'),
                     ('date_invoice', '>', self.from_date), ('date_invoice', '<', self.to_date)])
                row += 3
                sheet.merge_range('A{}:F{}'.format(row, row),
                                  'NOTA DE CREDITO ELECTRONICA (NOTA DE CREDITO COMPRA ELECTRONICA)',
                                  merge_format_total_text)
                row += 1
                for ref in invoice_refund:
                    ref_value = ref.reference
                    if not ref_value:
                        ref_value = ''
                    sheet.write('B{}'.format(str(row)), ref_value, merge_format_string)
                    sheet.write('C{}'.format(str(row)), ref.number, merge_format_string)
                    sheet.write('D{}'.format(str(row)), ref.date_invoice.strftime("%d/%m/%Y"), merge_format_string)
                    rut = ref.partner_id.invoice_rut
                    if not rut:
                        rut = ''
                    sheet.write('E{}'.format(str(row)), rut, merge_format_string)
                    sheet.write('F{}'.format(str(row)), ref.partner_id.display_name, merge_format_string)
                    sheet.write('H{}'.format(str(row)), round(ref.amount_untaxed_invoice_signed), merge_format_number)
                    sheet.write('I{}'.format(str(row)), round(ref.amount_total_signed), merge_format_number)
                    days = self.diff_dates(ref.date_invoice, today)
                    if days > 90:
                        sheet.write('K{}'.format(str(row)), round(ref.amount_tax), merge_format_number)
                        sheet.write('J{}'.format(str(row)), '0', merge_format_number)
                    else:
                        sheet.write('K{}'.format(str(row)), '0', merge_format_number)
                        sheet.write('J{}'.format(str(row)), round(ref.amount_tax), merge_format_number)
                    sheet.write_formula('L{}'.format(str(row)), '=SUM(H{}:J{})'.format(str(row), str(row)),
                                        merge_format_number)
                    row += 1
                sheet.merge_range('A{}:F{}'.format((row + 1), (row + 1)),
                                  'Total NOTA DE CREDITO ELECTRONICA (NOTA DE CREDITO COMPRA ELECTRONICA)',
                                  merge_format_total_text)
                sheet.write('G{}'.format(str(total)), str(len(invoice)), merge_format_total)
                sheet.write_formula('H{}'.format(str(total)), '=SUM(H{}:H{})'.format((row - len(invoice_refund)), row),
                                    merge_format_total)
                sheet.write_formula('I{}'.format(str(total)), '=SUM(I{}:I{})'.format((row - len(invoice_refund)), row),
                                    merge_format_total)
                sheet.write_formula('J{}'.format(str(total)), '=SUM(J{}:J{})'.format((row - len(invoice_refund)), row),
                                    merge_format_total)
                sheet.write_formula('K{}'.format(str(total)), '=SUM(K{}:K{})'.format((row - len(invoice_refund)), row),
                                    merge_format_total)
                sheet.write_formula('L{}'.format(str(total)), '=SUM(L{}:L{})'.format((row - len(invoice_refund)), row),
                                    merge_format_total)
            workbook.close()
            with open(file_name, "rb") as file:
                file_base64 = base64.b64encode(file.read())
            self.write({'purchase_file': file_base64,
                        'purchase_report_name': 'Libro de Compra.xlsx'})
            return {
                "type": "ir.actions.do_nothing",
            }

    @api.multi
    def generate_purchase_book(self):
        for item in self:
            file_name = 'temp'
            array_worksheet = []
            today = date.today()
            companies = self.env['res.company'].search(
                [('id', '=', self.env.user.company_id.id)], order='id asc')
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
                merge_format_number = workbook.add_format({
                    'bold': 0,
                    'align': 'center',
                    'valign': 'vcenter',
                    'num_format': '0,000'
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
                    'num_format': '0,000'
                })
                merge_format_total_text = workbook.add_format({
                    'border': 1,
                    'bold': 1,
                    'align': 'left',
                    'valign': 'vcenter'
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

                invoice = self.env['account.invoice'].search(
                    [('company_id.id', '=', company.id), ('type', '=', 'in_invoice'), ('state', '=', 'paid'),
                     ('date_invoice', '>', self.from_date), ('date_invoice', '<', self.to_date)])
                row = 14
                sheet.merge_range('A13:F13', 'Factura de compra electronica. (FACTURA COMPRA ELECTRONICA)',
                                  merge_format_total_text)
                for inv in invoice:
                    sheet.write('B{}'.format(str(row)), inv.reference, merge_format_string)
                    sheet.write('C{}'.format(str(row)), inv.number, merge_format_string)
                    sheet.write('D{}'.format(str(row)), inv.date_invoice.strftime("%d/%m/%Y"), merge_format_string)
                    rut = inv.partner_id.invoice_rut
                    if not rut:
                        rut = ''
                    sheet.write('E{}'.format(str(row)), rut, merge_format_string)
                    sheet.write('F{}'.format(str(row)), inv.partner_id.display_name, merge_format_string)
                    sheet.write('H{}'.format(str(row)), round(inv.amount_untaxed_invoice_signed), merge_format_number)
                    sheet.write('I{}'.format(str(row)), round(inv.amount_total_signed), merge_format_number)
                    days = self.diff_dates(inv.date_invoice, today)
                    if days > 90:
                        sheet.write('K{}'.format(str(row)), round(inv.amount_tax), merge_format_number)
                        sheet.write('J{}'.format(str(row)), '0', merge_format_number)
                    else:
                        sheet.write('K{}'.format(str(row)), '0', merge_format_number)
                        sheet.write('J{}'.format(str(row)), round(inv.amount_tax), merge_format_number)
                    sheet.write_formula('L{}'.format(str(row)), '=SUM(H{}:J{})'.format(str(row), str(row)),
                                        merge_format_number)
                    row += 1
                total = row + 1
                sheet.merge_range('A{}:F{}'.format((row + 1), (row + 1)),
                                  'Total Factura de compra electronica. (FACTURA COMPRA ELECTRONICA)',
                                  merge_format_total_text)
                sheet.write('G{}'.format(str(total)), str(len(invoice)), merge_format_total)
                sheet.write_formula('H{}'.format(str(total)), '=SUM(H{}:H{})'.format((row - len(invoice)), row),
                                    merge_format_total)
                sheet.write_formula('I{}'.format(str(total)), '=SUM(I{}:I{})'.format((row - len(invoice)), row),
                                    merge_format_total)
                sheet.write_formula('J{}'.format(str(total)), '=SUM(J{}:J{})'.format((row - len(invoice)), row),
                                    merge_format_total)
                sheet.write_formula('K{}'.format(str(total)), '=SUM(K{}:K{})'.format((row - len(invoice)), row),
                                    merge_format_total)
                sheet.write_formula('L{}'.format(str(total)), '=SUM(L{}:L{})'.format((row - len(invoice)), row),
                                    merge_format_total)
                invoice_refund = self.env['account.invoice'].search(
                    [('company_id.id', '=', company.id), ('type', '=', 'in_refund'), ('state', '=', 'paid'),
                     ('date_invoice', '>', self.from_date), ('date_invoice', '<', self.to_date)])
                row += 3
                sheet.merge_range('A{}:F{}'.format(row , row),
                                  'NOTA DE CREDITO ELECTRONICA (NOTA DE CREDITO COMPRA ELECTRONICA)',
                                  merge_format_total_text)
                row += 1
                for ref in invoice_refund:
                    ref_value = ref.reference
                    if not ref_value:
                        ref_value = ''
                    sheet.write('B{}'.format(str(row)), ref_value, merge_format_string)
                    sheet.write('C{}'.format(str(row)), ref.number, merge_format_string)
                    sheet.write('D{}'.format(str(row)), ref.date_invoice.strftime("%d/%m/%Y"), merge_format_string)
                    rut = ref.partner_id.invoice_rut
                    if not rut:
                        rut = ''
                    sheet.write('E{}'.format(str(row)), rut, merge_format_string)
                    sheet.write('F{}'.format(str(row)), ref.partner_id.display_name, merge_format_string)
                    sheet.write('H{}'.format(str(row)), round(ref.amount_untaxed_invoice_signed), merge_format_number)
                    sheet.write('I{}'.format(str(row)), round(ref.amount_total_signed), merge_format_number)
                    days = self.diff_dates(ref.date_invoice, today)
                    if days > 90:
                        sheet.write('K{}'.format(str(row)), round(ref.amount_tax), merge_format_number)
                        sheet.write('J{}'.format(str(row)), '0', merge_format_number)
                    else:
                        sheet.write('K{}'.format(str(row)), '0', merge_format_number)
                        sheet.write('J{}'.format(str(row)), round(ref.amount_tax), merge_format_number)
                    sheet.write_formula('L{}'.format(str(row)), '=SUM(H{}:J{})'.format(str(row), str(row)),
                                        merge_format_number)
                    row += 1
                sheet.merge_range('A{}:F{}'.format((row + 1), (row + 1)),
                                  'Total NOTA DE CREDITO ELECTRONICA (NOTA DE CREDITO COMPRA ELECTRONICA)',
                                  merge_format_total_text)
                sheet.write('G{}'.format(str(total)), str(len(invoice)), merge_format_total)
                sheet.write_formula('H{}'.format(str(total)), '=SUM(H{}:H{})'.format((row - len(invoice_refund)), row),
                                    merge_format_total)
                sheet.write_formula('I{}'.format(str(total)), '=SUM(I{}:I{})'.format((row - len(invoice_refund)), row),
                                    merge_format_total)
                sheet.write_formula('J{}'.format(str(total)), '=SUM(J{}:J{})'.format((row - len(invoice_refund)), row),
                                    merge_format_total)
                sheet.write_formula('K{}'.format(str(total)), '=SUM(K{}:K{})'.format((row - len(invoice_refund)), row),
                                    merge_format_total)
                sheet.write_formula('L{}'.format(str(total)), '=SUM(L{}:L{})'.format((row - len(invoice_refund)), row),
                                    merge_format_total)
            workbook.close()
            with open(file_name, "rb") as file:
                file_base64 = base64.b64encode(file.read())
            self.write({'purchase_file': file_base64,
                        'purchase_report_name': 'Libro de Compra.xlsx'})
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
        sheet.write('G11', ' ', format)
        sheet.write('H11', 'EXENTO', format)
        sheet.write('I11', 'NETO', format)
        sheet.write('J11', 'IVA', format)
        sheet.write('K11', 'IVA NO RECUPERABLE', format)
        sheet.write('L11', 'Total', format)
        return sheet

    def set_size(self, sheet):
        sheet.set_column('F:F', 40)
        sheet.set_column('B:B', 17.56)
        sheet.set_column('H:H', 11)
        sheet.set_column('J:J', 11)
        sheet.set_column('I:I', 12.56)
        sheet.set_column('L:L', 20)
        sheet.set_column('A:A', 6)
        sheet.set_column('D:D', 10)
        sheet.set_column('E:E', 12)
        sheet.set_column('C:C', 11)
        sheet.set_column('K:K', 20)
        sheet.set_column('G:G', 2.89)
        sheet.set_column('C:C', 15.89)
        sheet.set_column('F:F', 45)
        sheet.set_row(9, 6)
        return sheet

    def diff_dates(self, date1, date2):
        return abs(date2 - date1).days
