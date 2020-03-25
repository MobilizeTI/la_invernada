from odoo import fields, models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_assign(self):
        return True
