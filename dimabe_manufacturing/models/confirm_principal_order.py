from odoo import models,fields,api
import base64

class ConfirmPrincipalOrde(models.TransientModel):
    _name = 'confirm.principal.order'

    sale_ids = fields.Many2many('sale.order')

    sale_id = fields.Many2one('sale.order')

    picking_id = fields.Many2one('stock.picking')

    picking_ids = fields.Many2many('stock.picking')

    # @api.one
    # def select(self):
    #     for item in self.picking_ids:
    #         item.clean_reserved(item)
    #         move_line = self.env['stock.move.line'].create({
    #             'move_id':item.move_ids_without_package.filtered(lambda a:a.product_id.id == )
    #         })
    #
    # @api.one
    # def cancel(self):
    #     report = self.env.ref('dimabe_export_order.action_packing_list').render_qweb_pdf(
    #         self.picking_id.id)
    #     for item in self.picking_id.dispatch_line_ids:
    #         item.dispatch_id.write({
    #             'packing_list_file': base64.b64encode(report[0])
    #         })