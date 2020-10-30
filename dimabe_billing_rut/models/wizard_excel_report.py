from odoo import models,api,fields
class wizard_excel_report(models.Model):
    _name= "wizard.excel.report"
    excel_file = fields.Binary('excel file')
    file_name = fields.Char('Excel File', size=64)
