from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.float_utils import float_compare
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF, DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.exceptions import UserError, ValidationError

STATES = {'draft': [('readonly', False),]}


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    @api.model
    def _get_domain_for_picking_no_done(self):
        return [
            ('state','not in',('draft', 'done', 'cancel')),
            ('scheduled_date','<',fields.Datetime.now()),
        ]
        
    @api.model
    def _get_picking_no_done(self):
        return self.search(self._get_domain_for_picking_no_done(), order="scheduled_date")

    @api.model
    def send_mail_picking_no_done_on_date(self):
        picking_to_sent = self._get_picking_no_done()
        if picking_to_sent:
            template = self.env.ref('generic_stock_report.et_picking_no_done_on_date')
            template.with_context(picking_to_sent_ids=picking_to_sent.ids).action_sent_mail(picking_to_sent[0])
        return True
