# -*- coding: utf-8 -*-
# Copyright 2013-15 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright 2017 Jacques-Etienne Baudoux <je@bcim.be>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.onchange('purchase_id')
    def purchase_order_change(self):
        process_picking = False
        if self.purchase_id:
            process_picking = True
        res = super(AccountInvoice, self).purchase_order_change()
        if process_picking:
            if self.type == 'in_invoice':
                picking_ids = self.invoice_line_ids.mapped(
                    'move_line_ids'
                ).filtered(
                    lambda x: x.state == 'done' and
                    not x.location_dest_id.scrap_location and
                    x.location_dest_id.usage == 'internal'
                ).mapped('picking_id')
            else:
                picking_ids = self.invoice_line_ids.mapped(
                    'move_line_ids'
                ).filtered(
                    lambda x: x.state == 'done' and
                    not x.location_dest_id.scrap_location and
                    (x.location_id.usage == 'internal' and x.to_refund)
                ).mapped('picking_id')
            self.picking_ids = picking_ids
        return res

    @api.multi
    def _prepare_invoice_line_from_po_line(self, line):
        vals = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(line)
        if self.env.context.get('type', '') == 'in_refund':
            move_ids = line.mapped('move_ids').filtered(
                lambda x: x.state == 'done' and
                not x.invoice_line_ids and
                not x.location_dest_id.scrap_location and
                (x.location_id.usage == 'internal' and x.to_refund
                )).ids
        else:
            move_ids = line.mapped('move_ids').filtered(
                lambda x: x.state == 'done' and
                not x.invoice_line_ids and
                not x.location_dest_id.scrap_location and
                x.location_dest_id.usage == 'internal').ids
        vals['move_line_ids'] = [(6, 0, move_ids)]
        return vals
