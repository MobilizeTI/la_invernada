import pytz
from datetime import datetime

from odoo import models
from odoo.report import report_sxw
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class transfer_requisition_list_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(transfer_requisition_list_parser, self).__init__(cr, uid, name, context=context)
        report_lines = self.pool.get('transfer.requisition').get_lines_for_report_analisis(cr, uid, time_zone_pg="", context=context)
        util_obj = self.pool.get('odoo.utils')
        fields_obj = self.pool.get('ir.fields.converter')
        tz_name = fields_obj._input_tz(cr, uid, context)
        date_start = context.get('date_start', False)
        date_end = context.get('date_end', False)
        start_date_tz, end_date_tz = "", ""
        dates_string = ""
        if date_start:
            start_date_tz = util_obj._change_time_zone(cr, uid, datetime.strptime(date_start, DTF), pytz.UTC, tz_name, context=context)
            dates_string += " desde %s" % (start_date_tz.strftime(DTF))
        if date_end:
            end_date_tz = util_obj._change_time_zone(cr, uid, datetime.strptime(date_end, DTF), pytz.UTC, tz_name, context=context)
            dates_string += " hasta %s" % (end_date_tz.strftime(DTF))
        self.localcontext.update({'report_lines': report_lines,
                                  'dates_string': dates_string,
                                  })

class report_transfer_requisition_list(models.AbstractModel):
    _name = 'report.stock_transfers.report_transfer_requisition_list'
    _inherit = 'report.abstract_report'
    _template = 'stock_transfers.report_transfer_requisition_list'
    _wrapped_report_class = transfer_requisition_list_parser

