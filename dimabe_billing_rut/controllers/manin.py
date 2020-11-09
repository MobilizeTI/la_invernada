import json

from odoo import http
import datetime
import time
import json
import datetime
import io
from odoo.http import content_disposition, request

from odoo.addons.web.controllers.main import _serialize_exception

from odoo.tools import html_escape
from odoo.tools import date_utils

class XLSXReportController(http.Controller):

    @http.route('/api/xlsx_report', type='json', methods=['GET'], auth='token', cors='*')

    def get_report_xlsx(self, model, output_format, report_name, **kw):

        uid = request.session.uid

        report_obj = request.env[model].sudo(uid)
        data = {
            'start_date': time.strftime('%Y-%m-01'),
            'end_date': datetime.datetime.now()
        }

        options = json.loads(json.dumps(data, default=date_utils.json_default))

        try:

            if output_format == 'xlsx':

                response = request.make_response(

                    None,

                    headers=[('Content-Type', 'application/vnd.ms-excel'), ('Content-Disposition', content_disposition(report_name + '.xlsx'))

                    ]

                )

                report_obj.get_xlsx_report(options, response)


            return response

        except Exception as e:

            se = _serialize_exception(e)

            error = {

                'code': 200,

                'message': 'Odoo Server Error',

                'data': se

            }

            return request.make_response(html_escape(json.dumps(error)))

