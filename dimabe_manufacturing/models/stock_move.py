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

    def _update_reserved_quantity(self, need, available_quantity, location_id, lot_id=None, package_id=None,
                                  owner_id=None, strict=True):
        try:
            return super(StockMove, self)._update_reserved_quantity(need, available_quantity, location_id, lot_id, package_id, owner_id, strict)
        except UserError:
            pass