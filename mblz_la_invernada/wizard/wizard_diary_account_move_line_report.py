import base64
from datetime import date
import string
import xlsxwriter
from odoo import fields, models, api
from collections import Counter
import logging
_logger = logging.getLogger('TEST report =======')

class WizardDiaryAccountMoveLine(models.TransientModel):
    _name = 'account.move.line.diary'
    _description = 'Wizard Libro Diario'

    book_file = fields.Binary("Libro Diario")
    company_get_id = fields.Many2one('res.company', 'Compañía')
    # book_report_name = fields.Char("Libro Diario")
    date = fields.Date('Fecha')

    def generate_diary_book_pdf(self):
        self.ensure_one()
        [data] = self.read()
        datas = {
            'ids': [],
            'model': 'account.move.line',
            'form': data
        }
        return self.env.ref('mblz_la_invernada.diary_book_pdf_report').report_action(self, data=datas, config=False)
    
    @api.multi
    def generate_diary_book(self):
        file_name = 'diario.xlsx'
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
                titles = ['Fecha', 'Diario', 'Cuenta', 'Cód.Cuenta', 'Analítica', 'Movimientos', 'Empresa', 'Débito', 'Crédito', 'Divisa', 'Match']
                # invoices_get_tax = self.env['account.invoice'].sudo().search(
                #     [('dte_type_id', '!=', None), ('company_id', '=', self.company_get_id.id),
                #      ('date', '>=', self.from_date), ('date', '<=', self.to_date)])
                # taxes_title = list(
                #     dict.fromkeys(invoices_get_tax.mapped('tax_line_ids').mapped('tax_id').mapped('name')))

                # titles.append('Total')
                sheet.merge_range(0, 0, 0, 2, self.company_get_id.display_name, formats['title'])
                sheet.merge_range(1, 0, 1, 2, self.company_get_id.invoice_rut, formats['title'])
                sheet.merge_range(2, 0, 2, 2,
                                  f'{self.company_get_id.city},Region {self.company_get_id.region_address_id.name}',
                                  formats['title'])
                sheet.merge_range(4, 3, 4, 6, 'Libro Diario', formats['title'])
                sheet.merge_range(5, 3, 5, 6, 'Libro Diario Ordenado por asiento', formats['title'])
                sheet.write(6, 8, 'Fecha', formats['title'])
                sheet.write(6, 9, date.today().strftime('%Y-%m-%d'), formats['title'])
                sheet.merge_range(6, 3, 6, 6, f'Fecha {self.date}', formats['title'])
                sheet.merge_range(7, 3, 7, 6, 'Moneda : Peso Chileno', formats['title'])
                row = 10
                col = 0
                
                for title in titles:
                    sheet.write(row, col, title, formats['title'])
                    col += 1
                row += 2
                col = 0
                # sheet.merge_range(row, col, row, 5, 'Boleta electrónica. (BOLETA ELECTRONICA)',
                #                   formats['title'])
                # row += 1
                # domain_moves = [('date', '>=', self.from_date),
                #      ('type', 'in', ('in_invoice', 'in_refund')),
                #      ('date', '<=', self.to_date), ('dte_type_id.code', '=', 39),
                #      ('journal_id.employee_fee', '=', True),
                #      ('company_id.id', '=', self.company_get_id.id)]
                # #cambio en Order
                # invoices = self.env['account.invoice'].sudo().search(domain_invoices, order='date asc, reference asc') #facturas electronicas
                moves = self.get_move_lines(self.date, self.company_get_id[0].id)
                begin = row
                row += 1
                data_invoice = self.set_data_for_excel(sheet, row, moves, titles, formats)
                #OKKKKK
                # invoice_total = data_invoice.get('total').get('total')
                # invoice_net = data_invoice.get('total').get('net')
                # invoice_tax = data_invoice.get('total').get('tax')
                sheet = data_invoice['sheet']
                row = data_invoice['row']
                count_invoice += data_invoice['count_invoice']
                
                # net_total = invoice_net 
                # tax_total = invoice_tax
                # total_total = invoice_total
                # net_tax_total = net_total
                # sheet.write(row + 3, col + 5, 'Total General', formats['title'])
                # sheet.write(row + 3, col + 6, count_invoice, formats['total']) #SUMA DOCUMENTOS
                # # sheet.write(row + 3, col + 7, exempt_total, formats['total'])
                # # sheet.write(row + 3, col + 8, net_tax_total, formats['total'])
                # sheet.write(row + 3, col + 7, net_total, formats['total'])
                # sheet.write(row + 3, col + 8, tax_total, formats['total'])
                # # sheet.write(row + 3, col + 11, 0, formats['total']) #TODO totoales iva no recuperable
                # sheet.write(row + 3, col + 9, total_total, formats['total'])

        workbook.close()
        with open(file_name, "rb") as file:
            file_base64 = base64.b64encode(file.read())
        file_name = 'Libro Diario {} {}.xlsx'.format(company_name, date.today().strftime("%d/%m/%Y"))
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
    
    def get_move_lines(self, date, company_id):
        domain = [
            ('date', '=', date),
            ('company_id.id', '=', company_id)
            ]
        res = []
        
        lines = self.env['account.move.line'].sudo().search(domain, order='date asc')
        moves = list(set([line.move_id for line in lines]))
        for move in moves:
            move_lines = lines.filtered(lambda l: l.move_id == move)
            res.append({
                'move': move,
                'lines': move_lines
            })
        
        return res
    
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
    
    def set_data_for_excel(self, sheet, row, invoices, titles, formats):
        _logger.info('LOG:  -->>>> moves {}'.format(invoices))
        for inv in invoices:
            col = 0
            data = self.set_data_invoice(sheet, col, row, inv, invoices, titles, formats)
            sheet = data['sheet']
            row = data['row']
            col = data['col']
            row += 1
            # if inv.id == invoices[-1].id:
            #     row += 2
            # else:
            #     row += 1
        # sheet.merge_range(row, 0, row, 5, 'Totales:', formats['text_total'])
        # col = 6
        count_invoice = len(invoices)
        # sheet.write(row, col, count_invoice, formats['total']) ## Cantidad Total de Documentos
        # col += 1
        # exempt_sum = 0
        # if employee_fee:
        #     sheet.write(row, col, sum(invoices.mapped('amount_untaxed')), formats['total']) ## Total neto 
        #     col += 1
        #     tax = sum(invoices.mapped('amount_tax'))
        #     sheet.write(row, col, tax, formats['total']) ## Total imptos
        #     col += 1
        #     sheet.write(row, col, abs(sum(invoices.mapped('amount_total'))), formats['total'])
        # else:
        #     exempt_sum = sum(invoices.mapped('invoice_line_ids').filtered(
        #     lambda a: 'Exento' in a.invoice_line_tax_ids.mapped('name') or len(
        #         a.invoice_line_tax_ids) == 0).mapped('price_subtotal'))
        #     sheet.write(row, col, exempt_sum, formats['total']) ## Total exento
        #     col += 1
        #     net_tax = sum(invoices.mapped('amount_untaxed')) - abs(exempt_sum)
        #     sheet.write(row, col, net_tax, formats['total']) ## Total exento
        #     col += 1
        #     sheet.write(row, col, sum(invoices.mapped('amount_untaxed')), formats['total'])
        #     # if exempt:
        #     #     sheet.write(row, col, sum(invoices.mapped('amount_untaxed_signed')), formats['total'])
        #     # else:
        #     #     sheet.write(row, col, sum(invoices.mapped('amount_untaxed_signed')), formats['total'])
        #     col += 1
        #     sheet.write(row, col, sum(
        #         invoices.mapped('tax_line_ids').filtered(lambda a: 'IVA' in a.tax_id.name).mapped('amount')),
        #                 formats['total'])
        #     col += 1
        #     sheet.write(row, col, 0, formats['total'])
        #     col += 1
        #     for tax in taxes_title:
        #         if tax in titles or str.upper(tax) in titles and 'Exento' not in tax:
        #             line = invoices.mapped('tax_line_ids').filtered(
        #                 lambda a: str.lower(a.tax_id.name) == str.lower(tax) or str.upper(
        #                     a.tax_id.name) == tax).mapped(
        #                 'amount')
        #             sheet.write(row, col, sum(line), formats['total'])
        #             col += 1
        #     sheet.write(row, col, abs(sum(invoices.mapped('amount_total'))), formats['total'])
        col = 0
        return {
            'sheet': sheet, 
            'row': row, 
            # 'total': {
            #     'total' : sum(invoices.mapped('amount_total')),
            #     'net' : sum(invoices.mapped('amount_untaxed')),
            #     'tax': sum(invoices.mapped('amount_tax')),
            #     'exempt': exempt_sum,
            # },
            'count_invoice': count_invoice
        }

    def set_data_invoice(self, sheet, col, row, inv, invoices, titles, formats):
        sheet.write(row, col, inv['move'].name, formats['string'])
        # col += 1
        row += 1
        # if inv.dte_folio:
        #     sheet.write(row, col, inv.dte_folio, formats['string'])
        #TODO esto es lo que debiera ir
        # if inv.sii_document_number:
        #     sheet.write(row, col, inv.sii_document_number, formats['string'])
        for line in inv['lines']:
            sheet.write(row, col, line.date.strftime('%Y-%m-%d'), formats['string'])  
            col += 1
            sheet.write(row, col, line.journal_id.name, formats['string'])
            col += 1
            sheet.write(row, col, line.account_id.name, formats['string'])
            col += 1
            sheet.write(row, col, line.account_id.code, formats['string'])
            col += 1
            sheet.write(row, col, line.analytic_account_id.name, formats['string'])
            col += 1
            sheet.write(row, col, line.ref, formats['string'])
            col += 1
            sheet.write(row, col, line.debit, formats['string'])
            col += 1
            sheet.write(row, col, line.credit, formats['string'])
            # col += 1
            # sheet.write(row, col, line.full_reconcile_id, formats['string'])
            row += 1
            col = col - 8
            # if line.reference:
            #     sheet.write(row, col, inv.reference, formats['string'])
            # col += 1
            # if inv.number:
            #     sheet.write(row, col, inv.number, formats['string'])
            # col += 1
            # if inv.date:
            #     sheet.write(row, col, inv.date.strftime('%Y-%m-%d'), formats['string'])
            # col += 1
            # if inv.partner_id.invoice_rut:
            #     sheet.write(row, col, inv.partner_id.invoice_rut, formats['string'])
            # col += 1
            # long_name = max(invoices.mapped('partner_id').mapped('display_name'), key=len)
            # sheet.set_column(col, col, len(long_name))
            # sheet.write(row, col, inv.partner_id.display_name, formats['string'])
            # col += 2

        # exempt_taxes = inv.invoice_line_ids.filtered(lambda a: a.sii_code == 0 and a.amount == 0.0)
        # affect_taxes = inv.invoice_line_ids.filtered(lambda a: a.sii_code == 14)

        # exempt_taxes = inv.invoice_line_ids.filtered(lambda a: 'Exento' in a.invoice_line_tax_ids.mapped('name'))
        # affect_taxes = inv.invoice_line_ids.filtered(lambda a: 'IVA Débito' in a.invoice_line_tax_ids.mapped('name'))
        # employee_fee_taxes = inv.invoice_line_ids.filtered(lambda a: 'Retención Boleta Honorarios' in a.invoice_line_tax_ids.mapped('name'))
        # if exempt_taxes:
        #     sheet.write(row, col, sum(exempt_taxes.mapped('price_subtotal')), formats['number'])
        #     col += 1
        #     net = inv.amount_untaxed_signed
        #     net_tax = net - abs(sum(exempt_taxes.mapped('price_subtotal')))
        #     sheet.write(row, col, net_tax, formats['number'])
        #     col += 1
            
        #     if inv.dte_type_id.id:
        #         sheet.write(row, col, inv.amount_untaxed, formats['number'])
        #         col += 1 

        #         sheet.write(row, col, inv.amount_tax, formats['number'])
        #         col += 1
        #         sheet.write(row, col, '0', formats['number'])
        #         col += 1
        #         for tax in taxes_title:
        #             if tax in titles or str.upper(tax) in titles and 'Exento' not in tax:
        #                 line = inv.tax_line_ids.filtered(
        #                     lambda a: str.lower(a.tax_id.name) == str.lower(tax) or str.upper(
        #                         a.tax_id.name) == tax).mapped(
        #                     'amount')
        #                 sheet.write(row, col, sum(line), formats['number'])
        #                 col += 1
        #         sheet.write(row, col, inv.amount_total_signed, formats['number'])
        #     else:
        #         sheet.write(row, col, sum(inv.invoice_line_ids.filtered(inv.invoice_line_ids.filtered(
        #             lambda a: 'Exento' not in a.invoice_line_tax_ids.mapped('name') or len(
        #                 a.invoice_line_tax_ids) != 0)).mapped('price_subtotal')), formats['number'])
        #         col += 1
        #         sheet.write(row, col, sum(inv.tax_line_ids.filtered(lambda a: 'IVA' in a.tax_id.name).mapped('amount')),
        #                     formats['number'])
        #         col += 1

        #         sheet.write(row, col, '0', formats['number'])
        #         col += 1
        #         for tax in taxes_title:
        #             if tax in titles or str.upper(tax) in titles and 'Exento' not in tax:
        #                 line = inv.tax_line_ids.filtered(
        #                     lambda a: str.lower(a.tax_id.name) == str.lower(tax) or str.upper(
        #                         a.tax_id.name) == tax).mapped(
        #                     'amount')
        #                 sheet.write(row, col, sum(line), formats['number'])
        #                 col += 1
        #         sheet.write(row, col, inv.amount_total_signed, formats['number'])
        # elif affect_taxes:
        #     sheet.write_number(row, col, 0, formats['number'])
        #     col += 1
        #     # sheet.write(row, col, inv.amount_untaxed_signed, formats['number'])
        #     net_tax = inv.amount_untaxed - abs(sum(exempt_taxes.mapped('price_subtotal')))
        #     sheet.write(row, col, net_tax, formats['number'])
        #     col += 1
        #     sheet.write(row, col, inv.amount_untaxed, formats['number']) ##Neto
        #     col += 1
        #     days = self.diff_dates(inv.date, date.today())
        #     if days <= 90:
        #         sheet.write(row, col,
        #                     sum(inv.tax_line_ids.filtered(lambda a: 'IVA' in a.tax_id.name).mapped('amount')),
        #                     formats['number'])
        #         col += 1
        #         sheet.write_number(row, col, 0, formats['number'])
        #         col += 1
        #     else:
        #         sheet.write_number(row, col, 0, formats['number'])
        #         col += 1
        #         # sheet.write(row, col, inv.amount_tax, formats['number'])
        #         sheet.write(row, col,
        #                     sum(inv.tax_line_ids.filtered(lambda a: 'IVA' in a.tax_id.name).mapped('amount')),
        #                     formats['number'])
        #         col += 1
        #     # for tax in taxes_title:
        #     #     if tax in titles or str.upper(tax) in titles and 'Exento' not in tax:
        #     #         line = inv.tax_line_ids.filtered(
        #     #             lambda a: str.lower(a.tax_id.name) == str.lower(tax) or str.upper(a.tax_id.name) == tax).mapped(
        #     #             'amount')
        #     #         sheet.write(row, col, sum(line), formats['number'])
        #     #         col += 1
        #     sheet.write(row, col, abs(inv.amount_total_signed), formats['number'])
        # elif employee_fee_taxes:
            # sheet.write_number(row, col, int(inv.amount_untaxed), formats['number'])
            # col += 1
            # # sheet.write(row, col, inv.amount_untaxed_signed, formats['number'])
            # # net_tax = inv.amount_untaxed - abs(sum(exempt_taxes.mapped('price_subtotal')))
            # sheet.write(row, col, int(inv.amount_tax), formats['number'])
            # col += 1
            # sheet.write(row, col, int(inv.amount_total_signed), formats['number']) ##Neto
            # col += 1
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
        # _logger.info('LOG. **** output para linea %r', line_out)

        return line_out


       