from odoo import models, fields, api

class CustomAccountInvoiceLine(models.Model):
    _name = "custom.account.invoice.line"

    invoice_id = fields.Many2one('account.invoice',string="Factura")

    product_id = fields.Many2one('product.product',string="Producto")

    account_id = fields.Many2one('account.account', string="Cuenta")

    quantity = fields.Float(string="Cantidad")

    uom_id = fields.Many2one('uom.uom',string="Unidad de medida")

    price_unit = fields.Float(string="Precio")

    invoice_tax_line_ids = fields.Many2many('account.tax', string="Impuestos")

    exempt = fields.Selection([
            ('1', 'No afecto o exento de IVA'),
            ('2', 'Producto o servicio no es facturable'),
            ('3', 'Garantía de depósito por envases, autorizados por Resolución especial'),
            ('4', 'Item No Venta'),
            ('5', 'Item a rebajar'),
            ('6', 'Producto/servicio no facturable negativo'),
            ('7', '')
            ], 'Tipo Exento', default='7')

    price_subtotal = fields.Float(string="Subtotal")



