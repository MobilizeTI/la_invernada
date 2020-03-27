from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_assign(self):
        raise models.ValidationError('{}'.format(self))
        res = super(StockMove, self)._action_assign()
        return res
