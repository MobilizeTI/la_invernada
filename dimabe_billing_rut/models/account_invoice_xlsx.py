from odoo import fields , models , api
import base64
import csv
import datetime
import io
import logging
import time
from datetime import datetime
import xlsxwriter
from dateutil import relativedelta

class AccountInvoiceXlsx(models.Model):
    _name = 'account.invoice.xlsx'

    report_file = fields.Binary("Libro de Compra")

    report_name = fields.Char("Reporte")

    both = fields.Boolean("Ambas")

    @api.multi
    def generate_book(self):
        for item in self:
            array_worksheet = []
            companies = self.env['res.company'].search([],order='id asc')
            workbook = xlsxwriter.Workbook(self.report_name,{'in_memory':True})
            for com in companies:
                worksheet = workbook.add_worksheet(com.display_name)
                array_worksheet.append({'company_name':com.display_name,'worksheet':worksheet})
            for wk in array_worksheet:
                sheet = wk['worksheet']
                merge_format_string = workbook.add_format({
                    'border': 0,
                    'align': 'center',
                    'valign': 'vcenter',
                })
                sheet.merge_range('A1:C1',wk['company_name'],merge_format_string)
            return {
                "type": "ir.actions.do_nothing",
            }