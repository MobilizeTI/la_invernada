from odoo import models, api, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF

class PurchaseOrder(models.Model):

    _inherit = 'purchase.order'
    
    warehouse_id = fields.Many2one('stock.warehouse', 'Almacen', 
        related='picking_type_id.warehouse_id')
    
    @api.one
    @api.constrains('partner_id', 'partner_ref', 'state')
    def _check_partner_ref(self):
        if self.partner_id and self.partner_ref and self.state not in ('cancel',):
            domain = [('state', 'not in', ('cancel',)),
                      ('partner_ref', '=', self.partner_ref),
                      ('partner_id', '=', self.partner_id.id),
                      ('company_id', '=', self.company_id.id),
                      ('id', '!=', self.id)]
            order_ids = self.search(domain, limit=1)
            if order_ids:
                raise UserError('La referencia del Proveedor debe ser unica.\n'\
                                'Ya existe otro documento con el numero: %s para el proveedor: %s' % 
                                (self.partner_ref, self.partner_id.display_name))
                
    @api.multi
    def action_update_account_analytic(self):
        self.ensure_one()
        analytic_model = self.env['account.analytic.default'].with_context(warehouse_id=self.warehouse_id.id)
        date = fields.Date.context_today(self)
        if self.date_order:
            date = self.date_order
        for purchase_line in self.order_line:
            rec = analytic_model.account_get(purchase_line.product_id.id, self.partner_id.commercial_partner_id.id, self.env.uid, date, company_id=self.company_id.id)
            purchase_line.write({'account_analytic_id': rec.analytic_id.id})
        return True
    
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    @api.multi
    def _prepare_stock_moves(self, picking):
        vals_move = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        #al tener descuento pasar eso al movimiento de stock
        for val in vals_move:
            val['discount'] = self.discount
        return vals_move
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(PurchaseOrderLine, self).onchange_product_id()
        rec = self.env['account.analytic.default'].account_get(self.product_id.id, self.order_id.partner_id.commercial_partner_id.id, self.env.uid,
                                                               fields.Date.today(), company_id=self.company_id.id)
        self.account_analytic_id = rec.analytic_id.id
        return res
    