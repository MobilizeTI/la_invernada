from odoo import models, fields, api
import base64
from datetime import date
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.addons import decimal_precision as dp


class ConfirmPrincipalOrde(models.TransientModel):
    _name = 'confirm.principal.order'

    sale_ids = fields.Many2many('sale.order')

    sale_id = fields.Many2one('sale.order')

    picking_id = fields.Many2one('stock.picking')

    custom_dispatch_line_ids = fields.Many2many('custom.dispatch.line')

    @api.one
    def select(self):
        self.process_data()
        self.custom_dispatch_line_ids.filtered(lambda x: x.sale_id.id == self.sale_id.id).dispatch_id.write({
            'consignee_id': self.custom_dispatch_line_ids.filtered(
                lambda x: x.sale_id.id == self.sale_id.id).dispatch_id.consignee_id.id,
            'notify_ids': [(4, n) for n in self.picking_id.notify_ids.mapped('id')]
        })
        report = self.env.ref('dimabe_export_order.action_packing_list').render_qweb_pdf(
            self.custom_dispatch_line_ids.filtered(lambda x: x.sale_id.id == self.sale_id.id).dispatch_id.id)
        for item in self.custom_dispatch_line_ids:
            item.dispatch_id.write({
                'packing_list_file': base64.b64encode(report[0])
            })

    @api.one
    def cancel(self):
        self.process_data()
        self.custom_dispatch_line_ids.filtered(lambda x: x.sale_id.id == self.sale_id.id).dispatch_id.write({
            'consignee_id': self.custom_dispatch_line_ids.filtered(
                lambda x: x.sale_id.id == self.sale_id.id).dispatch_id.consignee_id.id,
            'notify_ids': [(4, n) for n in self.picking_id.notify_ids.mapped('id')]
        })
        report = self.env.ref('dimabe_export_order.action_packing_list').render_qweb_pdf(
            self.custom_dispatch_line_ids.filtered(lambda x: x.sale_id.id == self.sale_id.id).dispatch_id.id)
        for item in self.picking_id.dispatch_line_ids:
            item.dispatch_id.write({
                'packing_list_file': base64.b64encode(report[0])
            })

    def process_data(self):
        for item in self.custom_dispatch_line_ids:
            if item.dispatch_id.id == self.picking_id.id:
                self.picking_id.button_validate()
                continue
            item.dispatch_id.clean_reserved(item.dispatch_id)
            for line in self.picking_id.move_line_ids_without_package.filtered(
                    lambda a: a.product_id.id == item.product_id.id):
                line.write({
                    'picking_id': item.dispatch_id.id,
                    'move_id': item.dispatch_id.move_ids_without_package.filtered(
                        lambda x: x.product_id.id == line.product_id and x.picking_id.id == item.dispatch_id.id)
                })
            self.check_backorder(self.custom_dispatch_line_ids.mapped('dispatch_id'))

    def inmediate_transfer(self, picking):
        pick_to_backorder = self.env['stock.picking']
        pick_to_do = self.env['stock.picking']
        if picking.state == 'draft':
            picking.action_confirm()
            if picking.state != 'assigned':
                picking.action_assign()
                if picking.state != 'assigned':
                    raise models.UserError((
                        "Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
        for move in picking.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
            for move_line in move.move_line_ids:
                move_line.qty_done = move_line.product_uom_qty
        if self.check_backorder(picking):
            pick_to_backorder |= picking
        pick_to_do |= picking

    def check_backorder(self, picking_ids):
            draft_picking_lst = picking_ids.\
                filtered(lambda x: x.state == 'draft').\
                sorted(key=lambda r: r.scheduled_date)
            draft_picking_lst.action_confirm()

            pickings_to_check = picking_ids.\
                filtered(lambda x: x.state not in [
                    'draft',
                    'cancel',
                    'done',
                ]).\
                sorted(key=lambda r: r.scheduled_date)
            pickings_to_check.action_assign()

            assigned_picking_lst = picking_ids.\
                filtered(lambda x: x.state == 'assigned').\
                sorted(key=lambda r: r.scheduled_date)
            quantities_done = sum(
                move_line.qty_done for move_line in
                assigned_picking_lst.mapped('move_line_ids').filtered(
                    lambda m: m.state not in ('done', 'cancel')))
            if not quantities_done:
                return assigned_picking_lst.action_immediate_transfer_wizard()
            if any([pick._check_backorder() for pick in assigned_picking_lst]):
                return assigned_picking_lst.action_generate_backorder_wizard()
            assigned_picking_lst.action_done()

