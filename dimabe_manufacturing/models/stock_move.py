from odoo import models
from odoo import fields, models, api,_


class StockMove(models.Model):
    _inherit = 'stock.move'

    is_from_child = fields.Boolean('Es hijo')

    # def _action_assign(self):
    #     res = super(StockMove, self)._action_assign()
    #     raise models.ValidationError(self)
    #     return res

    def _update_reserved_quantity(self, need, available_quantity, location_id, lot_id=None, package_id=None, owner_id=None, strict=True):
        try:
            if not self.production_id:
                return super(StockMove, self)._update_reserved_quantity(need, available_quantity, location_id, lot_id,
                                                                        package_id, owner_id, strict)
            else:
                pass
        except:
            pass