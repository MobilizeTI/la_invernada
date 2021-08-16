from odoo import models, api, fields, tools
from odoo.tools.translate import _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    @api.multi
    def action_cancel(self):
        for picking in self.mapped('picking_ids'):
            if picking.state == 'done':
                raise UserError("No puede cancelar este pedido, ya hay despachos realizados, intente anularlos primero")
        self.mapped('order_line').write({'amount_cost': 0})
        return super(SaleOrder, self).action_cancel()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    amount_cost = fields.Float(u'Total Costo', digits=dp.get_precision('Product Price'), readonly=True)
    
    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        res = {}
        if self.product_id and self.product_uom:
            if self.product_uom.category_id != self.product_id.uom_id.category_id:
                self.product_uom = self.product_id.uom_id.id
                warning = {'title': "Informacion para el usuario",
                           'message': "La unidad de medida seleccionada debe pertenecer a la misma categoria "\
                                        "que la Unidad de medida del producto: %s" % self.product_id.uom_id.category_id.name
                           }
                res['warning'] = warning
                res.setdefault('domain', {}).setdefault('product_uom', []).append(('category_id', '=', self.product_id.uom_id.category_id.id))
                return res
        res = super(SaleOrderLine, self)._onchange_product_id_check_availability()
        if self.product_id:
            if not res:
                res = {}
            res.setdefault('domain', {}).setdefault('product_uom', []).append(('category_id', '=', self.product_id.uom_id.category_id.id))
        return res
    
    @api.multi
    def _prepare_invoice_line(self, qty):
        vals = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        vals['amount_cost'] = self.amount_cost
        return vals
