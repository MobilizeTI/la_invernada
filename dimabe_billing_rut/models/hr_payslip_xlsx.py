from odoo import models

class HrPaySlipXlsx(models.AbstractModel):
    _name = 'report.dimabe_billing_rut.remunerations_book'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        payslip = self.env['hr.payslip'].search([('state','=','done')])
        for obj in payslip:
            report_name = obj.name
            bold = workbook.add_format({'bold': True})
            sheet.write(0, 0, obj.name, bold)