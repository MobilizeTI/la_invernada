from odoo import models,fields,api
import base64

class ConfirmPrincipalOrde(models.TransientModel):
    _name = 'confirm.principal.order'

    sale_ids = fields.Many2many('sale.order')

    sale_id = fields.Many2one('sale.order')

    picking_id = fields.Many2one('stock.picking')

    @api.one
    def select(self):
        self.picking_id.dispatch_line_ids.filtered(lambda a: a.sale_id.id == self.sale_id.id).write({
            'is_select':True
        })
        report = self.env.ref('dimabe_export_order.action_packing_list').render_qweb_pdf(self.picking_id.filtered(lambda a: a.is_select).dispatch_id.id)
        for item in self.picking_id.dispatch_line_ids:
            item.dispatch_id.write({
                'packing_list_file':base64.b64encode(report[0])
            })

    @api.one
    def cancel(self):
        report = self.env.ref('dimabe_export_order.action_packing_list').render_qweb_pdf(
            self.picking_id.id)
        for item in self.picking_id.dispatch_line_ids:
            item.dispatch_id.write({
                'packing_list_file': base64.b64encode(report[0])
            })