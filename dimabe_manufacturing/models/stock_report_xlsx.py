from odoo import fields, models, api
import xlsxwriter
from datetime import date
import base64


class StockReportXlsx(models.TransientModel):
    _name = 'stock.report.xlsx'

    year = fields.Integer('Cosecha')

    @api.multi
    def generate_excel_raw_report(self):
        file_name = 'temp_report.xlsx'
        workbook = xlsxwriter.Workbook(file_name)
        sheet = workbook.add_worksheet('Informe de Materia Prima')
        row = 0
        col = 0
        titles = [(1, 'Productor:'), (2, 'Lote:'), (3, 'Kilos Disponible:'), (4, 'Variedad:'), (5, 'Calibre:'),
                  (6, 'Ubicacion Sistema:'), (7, 'Producto:'), (8, 'N° Guia:'), (9, 'Año Cosecha:'),
                  (10, 'Kilos Recepcionados:'), (11, 'Fecha Creacion:'), (12, 'Series Disponible:'),
                  (13, 'Enviado a Proceso de:'), (14, 'Fecha de Envio:'), (15, 'Ubicacion Fisica:'),
                  (16, 'Observaciones:')]
        for title in titles:
            sheet.write(row, col, title[1])
            col += 1
        row += 1
        col = 0
        raw_categ = self.env['product.category'].sudo().search([('name', '=', 'Materia Prima')])
        lots = self.env['stock.production.lot'].sudo().search(
            [('product_id.categ_id.id', 'in', raw_categ.mapped('child_id').mapped('id'))])
        for lot in lots:
            sheet.write(row,col,lot.producer_id.display_name)
            col += 1
            sheet.write(row,col,lot.name)
            col += 1
            sheet.write(row,col,str(sum(lot.stock_production_lot_serial_ids.filtered(lambda a: not a.consumed).mapped('real_weight'))))
            row += 1
            col = 0
        workbook.close()
        with open(file_name, "rb") as file:
            file_base64 = base64.b64encode(file.read())
        report_name = f'Informe de Existencia Materia Prima {date.today().strftime("%d/%m/%Y")}.xlsx'
        attachment_id = self.env['ir.attachment'].sudo().create({
            'name': report_name,
            'datas_fname': file_name,
            'datas': file_base64
        })

        action = {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}?download=true'.format(attachment_id.id, ),
            'target': 'current',
        }
        return action
