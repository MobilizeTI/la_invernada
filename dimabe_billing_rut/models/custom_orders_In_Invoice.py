from odoo import models, fields, api

class CustomOrdersInInvoice(models.Model):
    _name = 'custom.orders.in.invoice'

    stock_picking_id = fields.Integer(string= 'Despacho Id', required=True)

    stock_picking_name = fields.Char(string= 'Despacho', required=True)

    order_id = fields.Integer(string= 'Pedido Id', required=True)

    order_name = fields.Char(string= 'Pedido', required=True)

    product_id = fields.Char(string= 'Producto', required=True)

    price = fields.Char(string= 'Precio', required=True)

    quantity = fields.Char(string= 'Cantidad', required=True)

    invoice_id = fields.Many2one(
        'account.invoice',
        ondelete='cascade',
        index=True,
        copy=False,
        string="Pedido",
    )