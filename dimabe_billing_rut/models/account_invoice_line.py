from odoo import models, fields, api
import json
from math import floor
import logging
_logger = logging.getLogger(__name__)


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

    # @api.onchange('invoice_line_tax_ids')
    # def onchange_tax_ids(self):
    #     # _logger.info('LOG:--->>> onchange taxline_ids {} invoice {}'.format(self.invoice_line_tax_ids, self.invoice_id))
    #     if self.invoice_line_tax_ids.sii_type == 'R':
    #         _logger.info('LOG:--->>> onchange tax_line_ids {} invoice {}'.format(self.invoice_id.tax_line_ids, self.invoice_id))
    #         # self.invoice_id.update({
    #         #     ''
    #         # })

    @api.multi
    def unlink(self):
        orders_to_invoice = self.env['custom.orders.to.invoice'].search(
            [('invoice_id', '=', self.invoice_id.id), ('order_id', '=', self.order_id),
             ('stock_picking_id', '=', self.stock_picking_id), ('product_id', '=', self.product_id.id)])
        if orders_to_invoice:
            orders_to_invoice.unlink()

        custom_invoice_line_ids = self.env['custom.account.invoice.line'].search(
            [('invoice_id', '=', self.invoice_id.id)])
        for custom_line in custom_invoice_line_ids:
            new_quantity = custom_line.quantity
            if custom_line.product_id.id == self.product_id.id:
                new_quantity = new_quantity - self.quantity
                if new_quantity > 0:
                    custom_line.write({'quantity': new_quantity})
                elif new_quantity == 0:
                    custom_line.unlink()

        res = super(AccountInvoiceLine, self).unlink()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            invoice_id = self.env['account.invoice'].search([('id', '=', vals['invoice_id'])])
            # if invoice_id.currency_id.name=="CLP" and invoice_id.allow_currency_conversion:
            #    vals.update(price_unit = self.roundclp(vals['price_unit'] * float('{:.2f}'.format(invoice_id.exchange_rate))))
            if vals.get('display_type', self.default_get(['display_type'])['display_type']):
                vals.update(price_unit=0, account_id=False, quantity=0)

            #Send info COMEX to dispatch
            if 'stock_picking_id' in vals.keys():
                stock_picking_id = self.env['stock.picking'].search([('id','=',vals['stock_picking_id'])])
                if stock_picking_id:
                    stock_picking_id.write({
                        'shipping_number': invoice_id.shipping_number,
                        'agent_id': invoice_id.agent_id.id,
                        'commission': invoice_id.commission,
                        'charging_mode': invoice_id.charging_mode,
                        'booking_number': invoice_id.booking_number,
                        'bl_number': invoice_id.bl_number,
                        'container_type': invoice_id.container_type.id,
                        'client_label': invoice_id.client_label,
                        'client_label_file': invoice_id.client_label_file,
                        'freight_value': invoice_id.freight_amount,
                        'safe_value': invoice_id.safe_amount,
                        'remarks': invoice_id.remarks_comex,
                        'shipping_company': invoice_id.shipping_company.id,
                        'ship': invoice_id.ship.id,
                        'ship_number': invoice_id.ship_number,
                        'type_transport': invoice_id.type_transport.id,
                        'departure_port': invoice_id.departure_port.id,
                        'arrival_port': invoice_id.arrival_port.id,
                        'etd': invoice_id.etd,
                        'eta': invoice_id.eta,
                        'departure_date': invoice_id.departure_date,
                        'arrival_date': invoice_id.arrival_date,
                        'customs_department': invoice_id.custom_department.id,
                        'transport': invoice_id.transport_to_port.name,
                        'consignee_id': invoice_id.consignee_id.id,
                        'notify_ids': [(6, 0, invoice_id.notify_ids.ids)],
                        'custom_notify_ids': [(6, 0, invoice_id.custom_notify_ids.ids)]
                    })



        
        return super(AccountInvoiceLine, self).create(vals_list)

    @api.multi
    def write(self, vals):
        res = super(AccountInvoiceLine, self).write(vals)
        custom_invoice_line = self.env['custom.account.invoice.line'].search(
            [('invoice_id', '=', self.invoice_id.id), ('product_id', '=', self.product_id.id)])
        for line in custom_invoice_line:
            line.write({
                'price_unit': self.price_unit
            })

        return res

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
