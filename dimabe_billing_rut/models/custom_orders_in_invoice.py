from odoo import models, fields, api

class CustomOrdersInInvoice(models.Model):
    _name = 'custom.orders.in.invoice'

    order_id = fields.Char(string= 'Id Pedido', required=True)

    order_name = fields.Char(string= 'Pedido', required=True)

    product_id = fields.Char(string= 'Producto', required=True)

    price = fields.Char(string= 'Precio', required=True)

    quantity = fields.Char(string= 'Cantidad', required=True)

    invoice_id = fields.Many2one(
        'account.invoice',
        ondelete='cascade',
        index=True,
        copy=False,
        string="Pedidos",
    )