from odoo import models


class PackingList(models.AbstractModel):
    _name = 'report.stock_picking.report_packing_list'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, stock_pickings):
        for obj in stock_pickings:
            report_name = obj.name
            sheet = workbook.add_worksheet(report_name[:31])
            bold = workbook.add_format({'bold': True})
            sheet.write(0, 0, obj.name, bold)
