# Copyright 2014-2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    #campos para NC y devoluciones
    devolution = fields.Boolean('Is Devolution?', copy=False)
    original_picking_id = fields.Many2one('stock.picking', 'Origin Picking', 
        required=False, index=True)
    returned_ids = fields.One2many('stock.picking', 
        'original_picking_id', 'Returned pickings')

    def action_see_returns(self):
        self.ensure_one()
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        action['domain'] = [
            ('original_picking_id', '=', self.id),
            ('devolution', '=', True)
        ]
        # choose the view_mode accordingly
        if len(self.returned_ids) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            action['views'] = [(res and res.id or False, 'form')]
            action['res_id'] = self.returned_ids.id or False
        return action
