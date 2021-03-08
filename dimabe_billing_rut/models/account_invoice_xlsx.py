import base64
from datetime import date

import xlsxwriter
from odoo import fields, models, api


class AccountInvoiceXlsx(models.Model):
    _name = 'account.invoice.xlsx'

    purchase_file = fields.Binary(
        "Libro de Compra")

    purchase_report_name = fields.Char("Reporte Compra",
                                       )

    sale_file = fields.Binary(
        "Libro de Venta")

    sale_report_name = fields.Char("Reporte Venta")

    from_date = fields.Date('Desde')

    to_date = fields.Date('Hasta')

    both = fields.Boolean("Ambas")

    @api.multi
    def generate_sale_book(self):
        for item in self:
            file_name = 'temp'
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
                sheet = self.set_size(sheet)
                formats = self.set_formats(workbook)
                region = self.env['region.address'].search([('id', '=', 1)])
                sheet = self.set_data_company(wk['company_object'], sheet, formats, region, 0)
                invoices = self.env['account.invoice'].search(
                    [('type', 'in', ('out_invoice', 'out_refund')), ('date_invoice', '>', self.from_date),
                     ('date_invoice', '<', self.to_date), ('dte_type_id.code', '=', 33)])
                row = 14
                sheet.merge_range('A{}:F{}'.format((row), (row)),
                                  'Factura de compra electronica. (FACTURA COMPRA ELECTRONICA)',
                                  formats['text_total'])
                row += 1
                begin = row
                for inv in invoices:
                    sheet = self.set_data_invoice(sheet, row, inv, formats)
                    if inv.id == invoices[-1].id:
                        end = row
                        row += 2
                    else:
                        row += 1

                sheet = self.set_total(sheet, begin, end, row, invoices, formats,
                                       'Total Factura de compra electronica. (FACTURA COMPRA ELECTRONICA)')
                row += 2
                begin = 0
                end = 0
                exempts = self.env['account.invoice'].search(
                    [('type', 'in', ('out_invoice', 'out_refund')), ('date_invoice', '>', self.from_date),
                     ('date_invoice', '<', self.to_date), ('dte_type_id.code', '=', 34)])
                sheet.merge_range('A{}:F{}'.format((row), (row)),
                                  'Factura de compra exenta electronica. (FACTURA COMPRA EXENTA ELECTRONICA)',
                                  formats['text_total'])
                row += 2
                begin = row
                for ex in exempts:
                    sheet = self.set_data_invoice(sheet, row, ex, formats)
                    if ex.id == exempts[-1].id:
                        end = row
                        row += 3
                    else:
                        row += 1
                sheet = self.set_total(sheet, begin, end, row, exempts, formats,
                                       'Total Factura de compra exenta electronica. (FACTURA COMPRA EXENTA ELECTRONICA)')
                row += 2
                begin = 0
                end = 0
                credit_notes = self.env['account.invoice'].search(
                    [('type', 'in', ('out_invoice', 'out_refund')), ('date_invoice', '>', self.from_date),
                     ('date_invoice', '<', self.to_date), ('dte_type_id.code', '=', 61)])
                sheet.merge_range('A{}:F{}'.format((row), (row)),
                                  'NOTA DE CREDITO ELECTRONICA (NOTA DE CREDITO COMPRA ELECTRONICA)',
                                  formats['text_total'])
                row += 2
                begin = row
                for note_cre in credit_notes:
                    sheet = self.set_data_invoice(sheet, row, note_cre, formats)
                    if note_cre.id == credit_notes[-1].id:
                        end = row
                        row += 3
                    else:
                        row += 1
                sheet = self.set_total(sheet, begin, end, row, credit_notes, formats,
                                       'Total Nota de Credito Electronica (NOTA DE CREDITO COMPRA ELECTRONICA)')
                row += 2
                begin = 0
                end = 0
                debit_notes = self.env['account.invoice'].search(
                    [('type', 'in', ('out_invoice', 'out_refund')), ('date_invoice', '>', self.from_date),
                     ('date_invoice', '<', self.to_date), ('dte_type_id.code', '=', 56)])
                sheet.merge_range('A{}:F{}'.format((row), (row)),
                                  'NOTA DE DEBITO ELECTRONICA (NOTA DE DEBITO COMPRA ELECTRONICA)',
                                  formats['text_total'])
                row += 2
                begin = row
                for note_deb in debit_notes:
                    sheet = self.set_data_invoice(sheet, row, note_deb, formats)
                    if note_deb.id == debit_notes[-1].id:
                        end = row
                        row += 3
                    else:
                        row += 1
                sheet = self.set_total(sheet, begin, end, row, debit_notes, formats,
                                       'Total Nota de Debito Electronica (NOTA DE CREDITO COMPRA ELECTRONICA)')
                row += 2
                company_name = wk['company_object'].display_name.replace('.', '')
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

    @api.multi
    def generate_purchase_book(self):
        for item in self:
            file_name = 'temp'
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
                sheet = self.set_size(sheet)
                formats = self.set_formats(workbook)
                region = self.env['region.address'].search([('id', '=', 1)])
                sheet = self.set_data_company(wk['company_object'], sheet, formats, region, 1)
                invoices = self.env['account.invoice'].search(
                    [('type', 'in', ('in_invoice', 'in_refund')), ('date_invoice', '>', self.from_date),
                     ('date_invoice', '<', self.to_date), ('dte_type_id.code', '=', 33)])
                row = 14
                sheet.merge_range('A{}:F{}'.format((row), (row)),
                                  'Factura de compra electronica. (FACTURA COMPRA ELECTRONICA)',
                                  formats['text_total'])
                row += 1
                begin = row
                for inv in invoices:
                    sheet = self.set_data_invoice(sheet, row, inv, formats)
                    if inv.id == invoices[-1].id:
                        end = row
                        row += 2
                    else:
                        row += 1

                sheet = self.set_total(sheet, begin, end, row, invoices, formats,
                                       'Total Factura de compra electronica. (FACTURA COMPRA ELECTRONICA)')
                row += 2
                begin = 0
                end = 0
                exempts = self.env['account.invoice'].search(
                    [('type', '=', 'in_invoice'), ('date_invoice', '>', self.from_date),
                     ('date_invoice', '<', self.to_date), ('dte_type_id.code', '=', 34)])
                sheet.merge_range('A{}:F{}'.format((row), (row)),
                                  'Factura de compra electronica. (FACTURA COMPRA EXENTA ELECTRONICA)',
                                  formats['text_total'])
                row += 2
                begin = row
                for ex in exempts:
                    sheet = self.set_data_invoice(sheet, row, ex, formats)
                    if ex.id == exempts[-1].id:
                        end = row
                        row += 3
                    else:
                        row += 1
                sheet = self.set_total(sheet, begin, end, row, exempts, formats,
                                       'Total Factura de compra electronica. (FACTURA COMPRA EXENTA ELECTRONICA)')
                row += 2
                begin = 0
                end = 0
                credit_notes = self.env['account.invoice'].search(
                    [('type', 'in', ('in_invoice', 'in_refund')), ('date_invoice', '>', self.from_date),
                     ('date_invoice', '<', self.to_date), ('dte_type_id.code', '=', 61)])
                sheet.merge_range('A{}:F{}'.format((row), (row)),
                                  'NOTA DE CREDITO ELECTRONICA (NOTA DE CREDITO COMPRA ELECTRONICA)',
                                  formats['text_total'])
                row += 2
                begin = row
                for note_cre in credit_notes:
                    sheet = self.set_data_invoice(sheet, row, note_cre, formats)
                    if note_cre.id == credit_notes[-1].id:
                        end = row
                        row += 3
                    else:
                        row += 1
                sheet = self.set_total(sheet, begin, end, row, credit_notes, formats,
                                       'Total NOTA DE CREDITO ELECTRONICA (NOTA DE CREDITO COMPRA ELECTRONICA)')
                row += 2
                begin = 0
                end = 0
                debit_notes = self.env['account.invoice'].search(
                    [('type', 'in', ('in_invoice', 'in_refund')), ('date_invoice', '>', self.from_date),
                     ('date_invoice', '<', self.to_date), ('dte_type_id.code', '=', 56)])
                sheet.merge_range('A{}:F{}'.format((row), (row)),
                                  'NOTA DE DEBITO ELECTRONICA (NOTA DE DEBITO COMPRA ELECTRONICA)',
                                  formats['text_total'])
                row += 2
                begin = row
                for note_deb in debit_notes:
                    sheet = self.set_data_invoice(sheet, row, note_deb, formats)
                    if note_deb.id == debit_notes[-1].id:
                        end = row
                        row += 3
                    else:
                        row += 1
                sheet = self.set_total(sheet, begin, end, row, debit_notes, formats,
                                       'Total NOTA DE CREDITO ELECTRONICA (NOTA DE CREDITO COMPRA ELECTRONICA)')
                row += 2
                company_name = wk['company_object'].display_name.replace('.', '')
        workbook.close()
        with open(file_name, "rb") as file:
            file_base64 = base64.b64encode(file.read())
        file_name = 'Libro de Compra {} {}.xlsx'.format(company_name, date.today().strftime("%d/%m/%Y"))
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

    def set_data_company(self, company, sheet, formats, region, book):
        sheet.merge_range('A1:C1', company.display_name, formats['string'])
        sheet.merge_range('A2:C2', company.invoice_rut, formats['string'])
        sheet.merge_range('A3:C3', '{},Region {}'.format(company.city, region.name.capitalize()),
                          formats['string'])
        if book == 0:
            sheet.merge_range('A5:L5', 'Libro de Ventas', formats['string'])
            sheet.merge_range('A6:L6', 'Libro de Ventas Ordenado por fecha', formats['string'])
        else:
            sheet.merge_range('A5:L5', 'Libro de Compras', formats['string'])
            sheet.merge_range('A6:L6', 'Libro de Compras Ordenado por fecha', formats['string'])
        sheet.write('K7', 'Fecha', formats['string'])
        sheet.write('L7', date.today().strftime('%Y-%m-%d'), formats['string'])
        sheet.merge_range('A8:L8', 'Desde : {} Hasta : {}'.format(self.from_date.strftime(
            "%d/%m/%Y"), self.to_date.strftime("%d/%m/%Y")), formats['string'])
        sheet.merge_range(
            'A9:L9', 'Moneda : Peso Chileno', formats['string'])
        sheet = self.set_title(sheet, formats['title'], book)
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

    def set_total(self, sheet, begin, end, row, invoices, formats, string=''):
        sheet.merge_range('A{}:F{}'.format((row), (row)),
                          string,
                          formats['text_total'])
        sheet.write('G{}'.format(str(row)), str(len(invoices)), formats['total'])
        if len(invoices) > 0:
            sheet.write_formula('H{}'.format(str(row)), '=SUM(H{}:H{})'.format(begin, end),
                                formats['total'])
        else:
            sheet.write('H{}'.format(str(row)), '0', formats['total'])
        if len(invoices) > 0:
            sheet.write_formula('I{}'.format(str(row)), '=SUM(I{}:I{})'.format(begin, end),
                                formats['total'])
        else:
            sheet.write('I{}'.format(str(row)), '0', formats['total'])
        if len(invoices) > 0:
            sheet.write_formula('J{}'.format(str(row)), '=SUM(J{}:J{})'.format(begin, end),
                                formats['total'])
        else:
            sheet.write('J{}'.format(str(row)), '0', formats['total'])
        if len(invoices) > 0:
            sheet.write_formula('K{}'.format(str(row)), '=SUM(K{}:K{})'.format(begin, end),
                                formats['total'])
        else:
            sheet.write('K{}'.format(str(row)), '0', formats['total'])
        if len(invoices) > 0:
            sheet.write_formula('L{}'.format(str(row)), '=SUM(L{}:L{})'.format(begin, end),
                                formats['total'])
        if len(invoices) > 0:
            sheet.write_formula('L{}'.format(str(row)), '=SUM(M{}:M{})'.format(begin, end),
                                formats['total'])
        else:
            sheet.write('L{}'.format(str(row)), '0', formats['total'])
        return sheet

    def set_title(self, sheet, format, book=0):
        sheet.write('A11', 'Cod.SII', format)
        sheet.write('B11', 'Folio', format)
        sheet.write('C11', 'Cor.Interno', format)
        sheet.write('D11', 'Fecha', format)
        sheet.write('E11', 'RUT', format)
        if book == 0:
            sheet.write('F11', 'Nombre de Cliente', format)
        else:
            sheet.write('F11', 'Nombre de Proveedor', format)
        sheet.write('G11', ' ', format)
        sheet.write('H11', 'EXENTO', format)
        sheet.write('I11', 'NETO', format)
        sheet.write('J11', 'IVA', format)
        sheet.write('K11', 'IVA NO RECUPERABLE', format)
        sheet.write('L11', 'OTROS IMPUESTOS', format)
        sheet.write('M11', 'Total', format)
        return sheet

    def set_data_invoice(self, sheet, row, inv, formats):
        sheet.write('A{}'.format(str(row)), inv.dte_type_id.code, formats['string'])
        if inv.reference:
            sheet.write('B{}'.format(str(row)), inv.reference, formats['string'])
            sheet.write('C{}'.format(str(row)), inv.number, formats['string'])
        sheet.write('D{}'.format(str(row)), inv.date_invoice.strftime("%d/%m/%Y"), formats['string'])
        rut = inv.partner_id.invoice_rut
        if not rut:
            rut = ''
        sheet.write('E{}'.format(str(row)), rut, formats['string'])
        sheet.write('F{}'.format(str(row)), inv.partner_id.display_name, formats['string'])
        taxes = inv.mapped('invoice_line_ids').filtered(
            lambda a: len(a.invoice_line_tax_ids) == 0)
        if taxes:
            sheet.write('H{}'.format(str(row)), sum(taxes.mapped('price_subtotal')), formats['number'])
            sheet.write('I{}'.format(str(row)), '0', formats['number'])
        else:
            sheet.write('H{}'.format(str(row)), '0', formats['number'])
            sheet.write('I{}'.format(str(row)), round(inv.amount_untaxed_signed), formats['number'])

        days = self.diff_dates(inv.date_invoice, date.today())
        if days > 90:
            sheet.write('K{}'.format(str(row)), round(inv.amount_tax), formats['number'])
            sheet.write('J{}'.format(str(row)), '0', formats['number'])
        else:
            sheet.write('K{}'.format(str(row)), '0', formats['number'])
            sheet.write('J{}'.format(str(row)), round(inv.amount_tax), formats['number'])

        another_taxes = self.get_another_taxes(inv)
        sheet.write('L{}'.format(str(row)), round(sum(another_taxes)))
        sheet.write('M{}'.format(str(row)), round(inv.amount_total_signed), formats['number'])
        return sheet

    def diff_dates(self, date1, date2):
        return abs(date2 - date1).days

    def get_another_taxes(self, inv):
        another = []
        for line in inv.mapped('invoice_line_ids'):
            if line.invoice_line_tax_ids and len(line.invoice_line_tax_ids) > 0:
                if 'IVA Crédito' not in line.invoice_line_tax_ids.mapped(
                    'name') or 'IVA Débito' not in line.invoice_line_tax_ids.mapped('name'):
                    another.append(line.price_subtotal)
        return another
