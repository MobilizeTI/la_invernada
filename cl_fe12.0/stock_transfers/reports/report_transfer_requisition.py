
from odoo import models
from odoo.report import report_sxw
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class transfer_requisition_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(transfer_requisition_parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'get_lines': self._get_lines_sort,
                                  })
        
    def _get_lines_sort(self, requisition):
        lines = [l for l in requisition.line_ids]
        lines.sort(key=lambda x: x.product_id.name)
        return lines

class report_transfer_requisition(models.AbstractModel):
    _name = 'report.stock_transfers.report_transfer_requisition'
    _inherit = 'report.abstract_report'
    _template = 'stock_transfers.report_transfer_requisition'
    _wrapped_report_class = transfer_requisition_parser

