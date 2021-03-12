from odoo import models
from odoo import fields, models, api,_
from odoo.exceptions import UserError, ValidationError
from odoo.tools.pycompat import izip
from odoo.tools.float_utils import float_round, float_compare, float_is_zero
from odoo.addons import decimal_precision as dp


class StockMove(models.Model):
    _inherit = 'stock.move'

    is_from_child = fields.Boolean('Es hijo')

    # def _action_assign(self):
    #     res = super(StockMove, self)._action_assign()
    #     raise models.ValidationError(self)
    #     return res
