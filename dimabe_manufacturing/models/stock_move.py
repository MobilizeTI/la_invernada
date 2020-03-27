from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_assign(self):
        raise models.ValidationError(self.production_id)
        res = super(StockMove, self)._action_assign()
        return res
