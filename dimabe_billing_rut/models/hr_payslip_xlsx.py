import xlsxwriter
from odoo import models


class HrPaySlipXlsx(models.AbstractModel):
    _name = 'report.dimabe_billing_rut.remunerations_book'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        payslip = self.env['hr.payslip'].search([('state', '=', 'done')])
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
        sheet.merge_range("B1:E1","Informe: Libro de Remuneraciones",merge_format)
        sheet.write(1, 1, "Mes a procesar :{}".format(indicadores_id[-1]))
        bold = workbook.add_format({'bold': True})
