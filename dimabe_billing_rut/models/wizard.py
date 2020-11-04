from odoo import api, fields ,models
from odoo.tools.misc import xlwt
import io
import xlsxwriter
import base64

class WizardHrPaySlip(models.TransientModel):
    _name = "wizard.hr.payslip"
    _description = 'XLSX Report'

    date_from = fields.Date(string='Start Date')

    date_to = fields.Date(string='End Date')

    report = fields.Binary()

    def _get_data(self):
        current_date = fields.Date.today()

        domain = []

        domain += [('date_from','>=',current_date,current_date,"<=",self.date_to)]

        res = self.env['hr.payslip'].search([])

        docargs = []

        docargs.append(
            {'key': ""}
        )

        return res

    @api.multi
    def print_report_xlsx(self):
        file_name = 'temp'
        workbook = xlsxwriter.Workbook(file_name, {'in_memory': True})
        worksheet = workbook.add_worksheet()
        row = 0
        col = 0
        for e in self._get_data():
            worksheet.write(row, col, e.name)
            col += 1
        row += 1
        workbook.close()
        with open(file_name, "rb") as file:
            file_base64 = base64.b64encode(file.read())
        self.report = file_name + '.xlsx'
        self.write({'report': file_base64 })
        return {
            "type": "ir.actions.do_nothing",
        }