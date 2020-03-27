from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_assign(self):
        res = super(StockMove, self)._action_assign()
        raise models.ValidationError('{}'.format(
            self.filtered(lambda m: m.state in ['confirmed', 'waiting', 'partially_available'])))
        return res
