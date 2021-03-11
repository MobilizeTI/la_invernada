import base64
from datetime import date
import string
import xlsxwriter
from odoo import fields, models, api
from collections import Counter


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
                region = self.env['region.address'].search([('id', '=', 1)])
                titles = ['Cod.SII', 'Folio', 'Cor.Interno', 'Fecha', 'RUT', 'Nombre', '#', 'EXENTO', 'NETO', 'IVA',
                          'IVA NO RECUPERABLE']
                invoices_get_tax = self.env['account.invoice'].sudo().search([])
                taxes_title = list(
                    dict.fromkeys(invoices_get_tax.mapped('tax_line_ids').mapped('tax_id').mapped('name')))
                for tax in taxes_title:
                    if tax != 'IVA Crédito' and tax != 'IVA Débito' and tax != 'Exento':
                        titles.append(tax.upper())
                        if taxes_title[-1] == tax:
                            titles.append('Total')
                sheet.merge_range(0, 0, 0, 2, self.env.user.company_id.display_name)
                sheet.merge_range(1, 0, 1, 2, self.env.user.company_id.invoice_rut)
                sheet.write(2, 0,
                            f'{self.env.user.company_id.city},Region {self.env.user.company_id.region_address_id.name}')
                sheet.write(4, 4, 'Libro Ventas')
                sheet.write(5, 4, 'Libro de Ventas Ordenado por fecha')
                sheet.write(6, 10, 'Fecha')
                sheet.write(6, 11, date.today().strftime('%Y-%m-%d'))
                sheet.write(7, 0, f'Desde {self.from_date} Hasta {self.to_date}')
                sheet.write(8, 0, 'Moneda : Peso Chileno')
                row = 12
                col = 0
                for title in titles:
                    sheet.write(row, col, title)
                    col += 1
                row += 2
                col = 0
                sheet.write(row, col, 'Factura de compra electronica. (FACTURA COMPRA ELECTRONICA)')
                row += 1
                invoices = self.env['account.invoice'].search(
                    [('date_invoice', '>', self.from_date),
                     ('date_invoice', '<', self.to_date), ('dte_type_id.code', '=', 33)])
                begin = row
                total_exempt = []
                for inv in invoices:
                    sheet.write(row, col, inv.dte_type_id.code)
                    col += 1
                    if inv.dte_folio:
                        sheet.write(row, col, inv.dte_folio)
                    col += 1
                    if inv.number:
                        sheet.write(row, col, inv.number)
                    col += 1
                    if inv.date_invoice:
                        sheet.write(row, col, inv.date_invoice.strftime('%Y-%m-%d'))
                    col += 1
                    if inv.partner_id.invoice_rut:
                        sheet.write(row, col, inv.partner_id.invoice_rut)
                    col += 1
                    sheet.write(row, col, inv.partner_id.display_name)
                    col += 2
                    taxes = inv.invoice_line_ids.filtered(
                        lambda a: 'Exento' in a.invoice_line_tax_ids.mapped('name') or len(a.invoice_line_tax_ids) == 0)
                    if taxes:
                        sheet.write(row, col, sum(taxes.mapped('price_subtotal')))
                        total_exempt.append({col: sum(taxes.mapped('price_subtotal'))})
                        col += 1
                        net = inv.amount_untaxed_signed

                        if sum(taxes.mapped('price_subtotal')) == net:
                            sheet.write(row, col, '0')
                            col += 1
                        else:
                            sheet.write(row, col, inv.amount_untaxed_signed)
                            col += 1
                    else:
                        sheet.write_number(row, col, 0)
                        col += 1
                        sheet.write(row, col, inv.amount_untaxed_signed)
                        col += 1
                        sheet.write(row, col,
                                    sum(inv.tax_line_ids.filtered(lambda a: 'IVA' in a.tax_id.name).mapped('amount')))
                        col += 1
                        sheet.write_number(row, col, 0)
                        col += 1
                        for tax in taxes_title:
                            if tax in titles or str.upper(tax) in titles and 'Exento' not in tax:
                                line = inv.tax_line_ids.filtered(
                                    lambda a: str.lower(a.tax_id.name) == str.lower(tax) or str.upper(
                                        a.tax_id.name) == tax).mapped(
                                    'amount')
                                sheet.write(row, col, sum(line))
                                col += 1
                    if inv.id == invoices[-1].id:
                        row += 2
                    else:
                        row += 1
                col = 0
                counter = Counter()
                for item in total_exempt:
                    counter.update(item)
                total_dict = dict(counter)
                sheet.write(row, 0, 'Totales:')
                for k in total_dict:
                    worksheet.write(row, k, total_dict[k])
                col = 0
                exempts = self.env['account.invoice'].search([('date_invoice', '>', self.from_date),
                                                              ('date_invoice', '<', self.to_date),
                                                              ('dte_type_id.code', '=', 34)])
                row += 2
                sheet.write(row, col, 'Factura de compra exenta electronica. (FACTURA COMPRA EXENTA ELECTRONICA)')
                row += 1
                for ex in exempts:
                    data = self.set_data_invoice(sheet, col, row, ex, taxes_title, titles)
                    sheet = data['sheet']
                    row = data['row']
                    row += 1
                    col = 0
                credit = self.env['account.invoice'].search([('date_invoice', '>', self.from_date),
                                                             ('date_invoice', '<', self.to_date),
                                                             ('dte_type_id.code', '=', 61)])
                row += 2
                sheet.write(row, col, 'NOTA DE CREDITO ELECTRONICA (NOTA DE CREDITO COMPRA ELECTRONICA)')
                row += 1

                for cre in credit:
                    data = self.set_data_invoice(sheet, col, row, cre, taxes_title, titles)
                    sheet = data['sheet']
                    row = data['row']
                    row += 1
                    col = 0
                debit = self.env['account.invoice'].search([('date_invoice', '>', self.from_date),
                                                            ('date_invoice', '<', self.to_date),
                                                            ('dte_type_id.code', '=', 56)])
                row += 2
                sheet.write(row, col, 'NOTA DE DEBITO ELECTRONICA (NOTA DE DEBITO COMPRA ELECTRONICA)')
                row += 1

                for deb in debit:
                    data = self.set_data_invoice(sheet, col, row, deb, taxes_title, titles)
                    sheet = data['sheet']
                    row = data['row']
                    row += 1
                    col = 0
                row += 2

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

    def set_data_invoice(self, sheet, col, row, inv, taxes_title, titles):
        total_result_exent = []
        sheet.write(row, col, inv.dte_type_id.code)
        col += 1
        if inv.dte_folio:
            sheet.write(row, col, inv.dte_folio)
        col += 1
        if inv.number:
            sheet.write(row, col, inv.number)
        col += 1
        if inv.date_invoice:
            sheet.write(row, col, inv.date_invoice.strftime('%Y-%m-%d'))
        col += 1
        if inv.partner_id.invoice_rut:
            sheet.write(row, col, inv.partner_id.invoice_rut)
        col += 1
        sheet.write(row, col, inv.partner_id.display_name)
        col += 2
        taxes = inv.invoice_line_ids.filtered(
            lambda a: 'Exento' in a.invoice_line_tax_ids.mapped('name') or len(a.invoice_line_tax_ids) == 0)
        if taxes:
            sheet.write(row, col, sum(taxes.mapped('price_subtotal')))
            total_result_exent.append({col: sum(taxes.mapped('price_subtotal'))})
            col += 1
            net = inv.amount_untaxed_signed
            models._logger.error(f'{inv.date_invoice} {net}')
            if sum(taxes.mapped('price_subtotal')) == net:
                sheet.write(row, col, '0')
                col += 1
            else:
                sheet.write(row, col, inv.amount_untaxed_signed)
                col += 1
        else:
            sheet.write_number(row, col, 0)
            col += 1
            sheet.write(row, col, inv.amount_untaxed_signed)
            col += 1
            sheet.write(row, col,
                        sum(inv.tax_line_ids.filtered(lambda a: 'IVA' in a.tax_id.name).mapped('amount')))
            total_result_exent.append(
                {col: sum(inv.tax_line_ids.filtered(lambda a: 'IVA' in a.tax_id.name).mapped('amount'))})
            col += 1
            sheet.write_number(row, col, 0)
            col += 1
            for tax in taxes_title:
                if tax in titles or str.upper(tax) in titles and 'Exento' not in tax:
                    line = inv.tax_line_ids.filtered(
                        lambda a: str.lower(a.tax_id.name) == str.lower(tax) or str.upper(a.tax_id.name) == tax).mapped(
                        'amount')
                    sheet.write(row, col, sum(line))
                    col += 1

        return {'sheet': sheet, 'row': row, 'total_exempt': total_result_exent}

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
