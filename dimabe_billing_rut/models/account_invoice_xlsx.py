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
            companies = self.env['res.company'].search([])
            workbook = xlsxwriter.Workbook(self.report_name,{'in_memory':True})
            for com in companies:
                worksheet = workbook.add_worksheet(com.display_name)
                array_worksheet.append({'company_name':com.display_name,'worksheet':worksheet})
            array = worksheet_company for wk in array_worksheet if 'EXPORT' in wk['company_name']
            raise models.ValidationError(array)
            return {
                "type": "ir.actions.do_nothing",
            }