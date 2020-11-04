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

    report = fields.Binary(default =lambda self: self.env['wizard.hr.payslip'].search([])[-1].report)

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
        sheet_service = workbook.add_worksheet(self.env['res.partner'].search([('id', '=', 423)]).display_name)
        sheet_export = workbook.add_worksheet(self.env['res.partner'].search([('id', '=', 1)]).display_name)
        merge_format_title = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })
        merge_format_string = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })
        merge_format_number = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '$#'
        })
        workbook.close()
        with open(file_name, "rb") as file:
            file_base64 = base64.b64encode(file.read())
        self.write({'report': file_base64 })
        return {
            "type": "ir.actions.do_nothing",
        }