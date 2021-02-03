from odoo import models, fields, api

class CustomAccountInvoiceLine(models.Model):
    _name = "custom.account.invoice.line"

    invoice_id = fields.Many2one('account.invoice',string="Factura")

    product_id = fields.Many2one('product.product',string="Producto")

    account_id = fields.Many2one('account.account', string="Cuenta")

    quantity = fields.Float(string="Cantidad")

    uom_id = fields.Many2one('uom.uom',string="Unidad de medida")

    price_unit = fields.Float(string="Precio")

    name = fields.Text(string="Descripción", required=True)

    price_subtotal = fields.Float(string="Subtotal")



