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

    price_subtotal = fields.Float(string="Subtotal", compute="_compute_price_subtotal")

    canning_quantity = fields.Float(string="Cantidad de Envases", compute="_compute_canning_quantiy")

    def _compute_price_subtotal(self):
        for item in self:
            if self.price_unit and self.quantity:
                self.price_subtotal = self.price_unit * self.quantity

    def _compute_canning_quantiy(self):
        for atr in self.product_id.attribute_value_ids:
            is_kg = atr.attribute_id.name.find('K')
            if atr.attribute_id.name == 'Tipo de envase' and is_kg != 1:
                value = atr.name.isdigit()
                raise models.ValidationError('{} valor {} de {}'.format(self.quantity,value,atr.name))
                self.canning_quantity = self.quantity / value
                





