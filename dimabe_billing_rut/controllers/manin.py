from odoo import http, exceptions, models
from odoo.http import request
from odoo.tools import date_utils
from datetime import date, timedelta
import json
import werkzeug


class XLSXReportController(http.Controller):

    @http.route('/api/order', type='json', method=['GET'], auth='public', cors='*')
    def get_report_xlsx(self):
        respond = request.env['hr.payroll.structure'].sudo().search([('name', '=', 'Codigo del Trabajo')])
        result = []
        for payslip in respond:
            raw_data = payslip.read()
            json_data = json.dumps(raw_data, default=date_utils.json_default)
            json_dict = json.loads(json_data)
            result.append(json_dict)
        return result
