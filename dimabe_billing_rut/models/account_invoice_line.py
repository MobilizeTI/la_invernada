from odoo import models, fields, api
from .custom_orders_to_invoice import CustomOrdersToInvoice as oti

class AccountInvoiceLine(models.Model):

    _inherit = 'account.invoice.line'

    exempt = fields.Selection([
            ('1', 'No afecto o exento de IVA'),
            ('2', 'Producto o servicio no es facturable'),
            ('3', 'Garantía de depósito por envases, autorizados por Resolución especial'),
            ('4', 'Item No Venta'),
            ('5', 'Item a rebajar'),
            ('6', 'Producto/servicio no facturable negativo'),
            ('7', '')
            ], 'Tipo Exento', default='7')

    order_id = fields.Integer(string="Id Pedido", readonly=True)

    order_name = fields.Char(string="Pedido", readonly=True)

    quantity_to_invoice = fields.Char(string="Cantidad por Facturar", readonly=True)

    dispatch = fields.Char(string="Despacho", readonly="True")

    stock_picking_id = fields.Integer(string="Stock Picking Id", readonly="True")

    @api.multi
    def unlink(self):
        orders_to_invoice = self.env['custom.orders.to.invoice'].search([('invoice_id','=',self.invoice_id.id),('order_id','=',self.order_id),('stock_picking_id','=',self.stock_picking_id),('product_id','=',self.product_id.id)])
        if orders_to_invoice:
            orders_to_invoice.unlink()
        res = super(AccountInvoiceLine, self).unlink()
        self._onchange_invoice_line()
        return res

    @api.multi
    def write(self):
        res = super(AccountInvoiceLine, self).write()
        self._onchange_invoice_line()
        return res

    def _onchange_invoice_line(self):
        custom_invoice_line = self.env['custom.account.invoice.line'].search([('invoice_id','=',self.invoice_id.id)])
        for custom_line in custom_invoice_line:
            sum_quantity = 0;
            for invoice_line in self.invoice_line_ids:
                if  custom_line.product_id == invoice_line.product_id.id:
                    sum_quantity += invoice_line.quantity
            if sum_quantity == 0:
                custom_line_to_delete = self.env['custom.account.invoice.line'].search([('id','=',custom_line.id)])
                if custom_line_to_delete:
                    custom_line_to_delete.unlink()
            else:
                custom_line.write({
                    'quantity': sum_quantity
                })
        
            
           

