import base64
from datetime import date

import xlsxwriter
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
            today = date.today()
            array_worksheet = []
            companies = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
            workbook = xlsxwriter.Workbook(file_name, {'in_memory': True, 'strings_to_numbers': True})
            for com in companies:
                worksheet = workbook.add_worksheet(com.display_name)
                array_worksheet.append({
                    'company_object': com, 'worksheet': worksheet
                })
            for wk in array_worksheet:
                sheet = wk['worksheet']
                sheet = self.set_size(sheet)
                formats = self.set_formats(workbook)
                region = self.env['region.address'].search([('id', '=', 1)])
                sheet.merge_range('A1:C1', wk['company_object'].display_name, formats['string'])
                sheet.merge_range('A2:C2',wk['company_object'].invoice_rut,formats['string'])
                sheet.merge_range('A3:C3','{},Region {}'.format(wk['company_object'].city,region.name.capitalize()),formats['string'])
                sheet.merge_range('A5:L5','Libro de Ventas',formats['string'])
                sheet.merge_range('A6:L6','Libro de Ventas Ordenado por fecha',formats['string'])
        workbook.close()
        with open(file_name, "rb") as file:
            file_base64 = base64.b64encode(file.read())
        self.write({'sale_file': file_base64,
                    'sale_report_name': 'Libro de Ventas.xlsx'})
        return {
            "type": "ir.actions.do_nothing",
        }

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
        return {
            'string': merge_format_string,
            'number': merge_format_number,
            'title': merge_format_title,
            'total': merge_format_total,
            'text_total': merge_format_total_text
        }
