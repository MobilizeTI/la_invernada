from odoo import models
import xlsxwriter,xlrd


class PackingList(models.AbstractModel):
    _name = 'report.stock_picking.report_packing_list'
    _inherit = 'report.report_xlsx.abstract'

    name = 'Test'

    workbook = xlsxwriter.Workbook('Packing List {}.xlsx'.format(name))


    def generate_xlsx_report(self, workbook):
            report_name = self.name
            sheet = workbook.add_worksheet(report_name[:31])
            bold = workbook.add_format({'bold': True})
            sheet.write(0, 0, self.name, bold)
