from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class StockBackorderConfirmation(models.TransientModel):    
    _inherit = 'stock.backorder.confirmation'

    @api.one
    def _process(self, cancel_backorder=False):
        res = super(StockBackorderConfirmation, self)._process(cancel_backorder)
        for picking in self.pick_ids:
            template = self.env.ref('generic_stock_report.et_picking_partial')
            for backorder in picking.backorder_ids:
                if backorder.state == 'cancel':
                    continue
                template.action_sent_mail(backorder)
        return res
