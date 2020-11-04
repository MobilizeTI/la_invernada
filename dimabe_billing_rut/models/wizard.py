from odoo import api, fields ,models
from odoo.tools.misc import xlwt
import io

class WizardHrPaySlip(models.TransientModel):
    _name = "wizard.hr.payslip"
    _description = 'XLSX Report'

    date_from = fields.Date(string='Start Date')

    date_to = fields.Date(string='End Date')

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
        workbook = xlwt.Workbook()

        companies = self.env['res.company'].search([]).mapped('partner_id').mapped('id')

        for com in companies:
            sheet = workbook.add_sheet(self.env['res.partner'].search([('id','=',com)]).name)

        sheet.row(3).height = 256 * 2

        sheet.write_merge(3,3,0,11,u'Libro de Remuneraciones')

        data = self._get_data()

        row = 8
        for h in data:
            sheet.write_merge(row,row,0,0)
            sheet.write_merge(row,row,1,1)
            row += 1

        stream = io.BytesIO()
        workbook.save(stream)

        WizardHrPaySlip()

        # Here report name is the name that’ll be printed for this report#

        return self.env.ref('report.dimabe_billing_rut.remunerations_book').report_action(self)

        return self.env.ref('').report_action(self)