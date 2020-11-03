import time
import json
import datetime
import io
from odoo import fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import date_utils

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class ExcelWizard(models.TransientModel):
    _name = "hr.payslip.xlsx.report.wizard"

    start_date = fields.Datetime(string="Fecha de Inicio", default=time.strftime('%Y-%m-01'), required=True)

    end_date = fields.Datetime(string="Fecha de Termino", default=datetime.datetime.now(), required=True)

    def print_xlsx(self):
        if self.start_date > self.end_date:
            raise ValidationError('La fecha de inicio no puede ser mayer a la fecha de termino')
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date
        }
        return {
            'type': 'ir_action_xlsx_download',
            'data': {'model': 'hr.payslip.xlsx.report.wizard',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Excel Report'
                     },
        }

    def get_xlsx_report(self, data, response):

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        sheet = workbook.add_worksheet()

        cell_format = workbook.add_format({'font_size': '12px'})

        head = workbook.add_format({'align': 'center', 'bold': True,'font_size':'20px'})

        txt = workbook.add_format({'font_size': '10px'})

        sheet.merge_range('B2:I3', 'EXCEL REPORT', head)

        sheet.write('B6', 'From:', cell_format)

        sheet.merge_range('C6:D6', data['start_date'],txt)

        sheet.write('F6', 'To:', cell_format)

        sheet.merge_range('G6:H6', data['end_date'],txt)

        workbook.close()

        output.seek(0)

        response.stream.write(output.read())

        output.close()

