import xlsxwriter
from odoo import models


class HrPaySlipXlsx(models.AbstractModel):
    _name = 'report.dimabe_billing_rut.remunerations_book'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        payslip = self.env['hr.payslip'].search([])
        report_name = "Libro de Remuneraciones"
        # One sheet by partner
        indicadores_id = payslip.mapped('indicadores_id').mapped('name')
        sheet = workbook.add_worksheet('Libro de Remuneraciones')
        merge_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            })
        sheet.merge_range("B2:E2","Informe: Libro de Remuneraciones",merge_format)
        sheet.merge_range("B3:E3","Mes a procesar : {}".format(indicadores_id[-1]),merge_format)
        employees = self.env['hr.employee'].search([('address_id','=',423)])
        row = 8
        column = 8
        for employee in employees:
            sheet.merge_range("B{}:D{}".format(row,column),employee.display_name,merge_format)
        bold = workbook.add_format({'bold': True})
