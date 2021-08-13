# Copyright 2016 Chafique DELLI @ Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests.common import TransactionCase


class TestPurchasePickingState(TransactionCase):

    def test_picking_state_in_purchase_order(self):
        draft_order_ids = self.env['purchase.order'].search([
            ('state', 'in', ['draft', 'sent', 'to approve', 'cancel']),
        ])
        for purchase in draft_order_ids:
            self.assertEqual(purchase.picking_state, 'draft')
        confirmed_order_ids = self.env['purchase.order'].search([
            ('state', 'in', ['purchase', 'done']),
        ])
        for purchase in confirmed_order_ids:
            pickings_state = set(
                [picking.state for picking in purchase.picking_ids])
            if pickings_state == set(['cancel']):
                self.assertEqual(purchase.picking_state, 'cancel')
            elif (pickings_state == set(['cancel', 'done']) or
                  pickings_state == set(['done'])):
                self.assertEqual(purchase.picking_state, 'done')
            elif 'done' in pickings_state:
                self.assertEqual(purchase.picking_state, 'partially_received')
            else:
                self.assertEqual(purchase.picking_state, 'not_received')
