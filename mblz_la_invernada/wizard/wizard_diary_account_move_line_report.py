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
                titles = ['Cod.SII', 'Folio', 'Cor.Interno', 'Fecha', 'RUT', 'Nombre', '#', 'NETO']
                # invoices_get_tax = self.env['account.invoice'].sudo().search(
                #     [('dte_type_id', '!=', None), ('company_id', '=', self.company_get_id.id),
                #      ('date', '>=', self.from_date), ('date', '<=', self.to_date)])
                # taxes_title = list(
                #     dict.fromkeys(invoices_get_tax.mapped('tax_line_ids').mapped('tax_id').mapped('name')))

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
                sheet.merge_range(6, 3, 6, 6, f'Fecha {self.date}', formats['title'])
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
                # domain_moves = [('date', '>=', self.from_date),
                #      ('type', 'in', ('in_invoice', 'in_refund')),
                #      ('date', '<=', self.to_date), ('dte_type_id.code', '=', 39),
                #      ('journal_id.employee_fee', '=', True),
                #      ('company_id.id', '=', self.company_get_id.id)]
                # #cambio en Order
                # invoices = self.env['account.invoice'].sudo().search(domain_invoices, order='date asc, reference asc') #facturas electronicas
                moves = self.get_move_lines(self.date, self.company_get_id[0])
                # begin = row
                # row += 1
                # data_invoice = self.set_data_for_excel(sheet, row, invoices, taxes_title, titles, formats, exempt=False, employee_fee=True)
                # #OKKKKK
                # invoice_total = data_invoice.get('total').get('total')
                # invoice_net = data_invoice.get('total').get('net')
                # invoice_tax = data_invoice.get('total').get('tax')
                # sheet = data_invoice['sheet']
                # row = data_invoice['row']
                # count_invoice += data_invoice['count_invoice']
                
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

       