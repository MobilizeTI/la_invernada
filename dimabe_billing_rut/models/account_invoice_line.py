from odoo import models, fields, api
import json

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
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            invoice_id = self.env['account.invoice'].search([('id','=',vals['invoice_id'])])
            if invoice_id.currency_id.name=="CLP":
                vals.update(price_unit = vals['price_unit'] * self.roundClp(invoice_id.exchange_rate))
            if vals.get('display_type', self.default_get(['display_type'])['display_type']):
                vals.update(price_unit=0, account_id=False, quantity=0)
        return super(AccountInvoiceLine, self).create(vals_list)

    def roundclp(self, value):
        value_str = str(value)
        list_value = value_str.split('.')
        if len(list_value) > 1:
            decimal = int(list_value[1][0])
            if decimal == 0:
                return int(value)
            elif decimal < 5:
                return floor(value)
            else:
                return round(value)
        else:
            return value

    

