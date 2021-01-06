from odoo import http, exceptions, models
from odoo.http import request
from datetime import date, timedelta
import werkzeug


class XLSXReportController(http.Controller):

    @http.route('/api/test', type='json', method=['GET'], auth='public', cors='*')
    def get_report_xlsx(self):
        respond = request.env['hr.payslip'].sudo().search([('state', '=', 'done')])
        result = []
        for payslip in respond:
            raw_data = payslip.read()
            result.append(type(raw_data))
        return result
