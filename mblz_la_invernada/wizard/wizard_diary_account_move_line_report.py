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
    date_from = fields.Date('Desde')
    date_to = fields.Date('Hasta')

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
                titles = ['Fecha', 'Diario', 'Cuenta', 'Cód.Cuenta', 'Analítica', 'Ref', 'Empresa', 'Débito', 'Crédito', 'Divisa', 'Match']
                sheet.merge_range(0, 0, 0, 2, self.company_get_id.display_name, formats['title'])
                sheet.merge_range(1, 0, 1, 2, self.company_get_id.invoice_rut, formats['title'])
                sheet.merge_range(2, 0, 2, 2,
                                  f'{self.company_get_id.city},Region {self.company_get_id.region_address_id.name}',
                                  formats['title'])
                sheet.merge_range(4, 3, 4, 6, 'Libro Diario', formats['title'])
                sheet.merge_range(5, 3, 5, 6, 'Libro Diario Ordenado por asiento', formats['title'])
                sheet.write(6, 8, 'Fecha Reporte', formats['title'])
                sheet.write(6, 9, date.today().strftime('%Y-%m-%d'), formats['title'])
                sheet.merge_range(6, 3, 6, 6, f'Desde: {self.date_from}', formats['title'])
                sheet.merge_range(7, 3, 7, 6, f'Hasta: {self.date_to}', formats['title'])
                sheet.merge_range(8, 3, 8, 6, 'Moneda : Peso Chileno', formats['title'])
                row = 10
                col = 0
                
                for title in titles:
                    sheet.write(row, col, title, formats['title'])
                    col += 1
                row += 2
                col = 0
                moves = self.get_move_lines(self.date_from, self.date_to, self.company_get_id[0].id)
                begin = row
                row += 1
                data_invoice = self.set_data_for_excel(sheet, row, moves, titles, formats)
                sheet = data_invoice['sheet']
                row = data_invoice['row']
                count_invoice += data_invoice['count_invoice']

        workbook.close()
        with open(file_name, "rb") as file:
            file_base64 = base64.b64encode(file.read())
        file_name = 'Libro Diario {} Desde {} Hasta {}.xlsx'.format(company_name, self.date_from.strftime("%d/%m/%Y"), self.date_to.strftime("%d/%m/%Y"))
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
    
    def get_move_lines(self, date_from, date_to, company_id):
        domain = [
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('company_id.id', '=', company_id)
            ]
        res = []
        
        lines = self.env['account.move.line'].sudo().search(domain, order='date asc')

        # moves = list(set([line.move_id for line in lines]))
        moves = []
        for l in lines:
            if l.move_id not in moves:
                moves.append(l.move_id)
        # moves = [line.move_id for line in lines]
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
        for inv in invoices:
            col = 0
            data = self.set_data_invoice(sheet, col, row, inv, invoices, titles, formats)
            sheet = data['sheet']
            row = data['row']
            col = data['col']
            row += 1
        count_invoice = len(invoices)
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
        sheet.write(row, col, inv['move'].name, formats['title'])
        # sheet.write(row, col, inv[0].move_id.name, formats['title'])
        width = len(inv['move'].name)
        sheet.set_column(col, row, width)
        row += 1
        total_debit, total_credit = 0.0, 0.0
        for line in inv['lines']:
            total_debit += line.debit
            total_credit += line.credit
            #Fecha
            sheet.write(row, col, line.date.strftime('%Y-%m-%d'), formats['string'])  
            col += 1
            #Diario
            sheet.write(row, col, line.journal_id.name, formats['string'])
            width = len(line.journal_id.name)
            col += 1
            sheet.set_column(col, row, width)
            
            #Cuenta (Nombre)
            sheet.write(row, col, line.account_id.name, formats['string'])
            width = len(line.account_id.name)
            col += 1
            sheet.set_column(col, row, width)
            
            #Cuenta (Código)
            sheet.write(row, col, line.account_id.code, formats['string'])
            col += 1
            #Cuenta Analítica
            if line.analytic_account_id:
                sheet.write(row, col, line.analytic_account_id.name, formats['string'])
                width = len(line.analytic_account_id.name)
            col += 1
            sheet.set_column(col, row, width)
            
            #Referencia
            sheet.write(row, col, line.ref, formats['string'])
            width = len(line.ref)
            col += 1
            sheet.set_column(col, row, width)
            
            #Partner
            if line.partner_id:
                sheet.write(row, col, line.partner_id.name, formats['string'])
                width = len(line.partner_id.name)
            col += 1
            sheet.set_column(col, row, width)
            #Débito
            sheet.write(row, col, line.debit, formats['number'])
            col += 1
            #Crédito
            sheet.write(row, col, line.credit, formats['number'])
            col += 1
            #Divisa
            if line.amount_currency:
                sheet.write(row, col, line.amount_currency, formats['number'])
            col += 1
            #Match
            if line.reconciled:
                sheet.write(row, col, line.full_reconcile_id.name, formats['string'])
            col = col - 10
            row += 1
        #Totales
        sheet.write(row, col + 6, 'Totales', formats['title'])
        sheet.write(row, col + 7, total_debit, formats['total'])
        sheet.write(row, col + 8, total_credit, formats['total'])
        
        line_out = {'sheet': sheet, 'row': row, 'col': col}

        return line_out


       