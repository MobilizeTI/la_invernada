from odoo import models
from odoo import fields, models, api,_


class StockMove(models.Model):
    _inherit = 'stock.move'

    is_from_child = fields.Boolean('Es hijo')

    # def _action_assign(self):
    #     res = super(StockMove, self)._action_assign()
    #     raise models.ValidationError(self)
    #     return res

