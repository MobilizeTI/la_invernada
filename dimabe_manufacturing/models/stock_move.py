from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    # def _action_assign(self):
    #     res = super(StockMove, self)._action_assign()
    #     raise models.ValidationError(self)
    #     return res


    @api.multi
    def