from odoo import models

class HrPaySlipXlsx(models.AbstractModel):
    _name = 'report.dimabe_billing_rut.remunerations_book'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        payslip = self.env['hr.payslip'].search([('state','=','done')])
        report_name = obj.name
        # One sheet by partner
        sheet = workbook.add_worksheet('Libro de Remuneraciones')
        bold = workbook.add_format({'bold': True})
