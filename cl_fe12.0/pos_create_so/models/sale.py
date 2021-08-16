# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from odoo import fields, models, api, _

class sale_order(models.Model):
    _inherit = "sale.order"
    
    @api.model
    def _prepare_sale_order_vals(self, customer_id, pos_config):
        order_vals = {
            'partner_id': customer_id,
        }
        if pos_config.crm_team_id:
            order_vals['team_id'] = pos_config.crm_team_id.id
        return order_vals
    
    @api.model
    def _prepare_invoice_payment(self, invoice, pos_payment_vals):
        journal= self.env['account.journal'].browse(pos_payment_vals.get('journal_id'))
        payment_vals = {
           'payment_type': 'inbound',
           'partner_id': invoice.partner_id.id,
           'partner_type': 'customer',
           'journal_id': journal.id or False,
           'amount': pos_payment_vals.get('amount'),
           'payment_method_id': journal.inbound_payment_method_ids.id,
           'invoice_ids': [(6, 0, [invoice.id])],
        }
        return payment_vals
    
    @api.multi
    def _post_process_order_line(self, pos_line_vals, sale_line, product):
        sale_line.update({
            'price_unit': pos_line_vals['price_unit'],
        })
        taxes = product.taxes_id.ids
        if not sale_line.get('tax_id'):
            sale_line.update({'tax_id': [(6, 0, taxes)]})
        return sale_line
    
    @api.multi
    def _prepare_order_line(self, pos_line_vals):
        Products = self.env['product.product']
        SaleOrderLines = self.env['sale.order.line']
        product = Products.browse(pos_line_vals['product_id'])
        sale_line = {
            'order_id': self.id,
            'name': product.name or False,
            'product_id': product.id,
            'product_uom': product.uom_id.id,
            'product_uom_qty': pos_line_vals['qty'],
            'discount': pos_line_vals.get('discount'),
        }
        new_prod = SaleOrderLines.new(sale_line)
        new_prod.product_id_change()
        sale_line = SaleOrderLines._convert_to_write({name: new_prod[name] for name in new_prod._cache})
        sale_line = self._post_process_order_line(pos_line_vals, sale_line, product)
        return sale_line
    
    @api.multi
    def _prepare_response_for_pos(self):
        response_pos = {
            'id': self.id,
            'name': self.name,
        }
        if self.picking_ids:
            response_pos['picking_id'] = self.picking_ids[0].id
            response_pos['picking_name'] = self.picking_ids[0].name
        if self.invoice_ids:
            response_pos['invoice_id'] = self.invoice_ids[0].id
            response_pos['invoice_name'] = self.invoice_ids[0].display_name
        return response_pos

    @api.model
    def create_sales_order(self, orderline, customer_id, pos_config_id, journals):
        SaleOrderLines = self.env['sale.order.line']
        pos_config = self.env['pos.config'].browse(pos_config_id)
        response_pos = {}
        if customer_id and pos_config:
            customer_id = int(customer_id)
            order_vals = self._prepare_sale_order_vals(customer_id, pos_config)
            new_sale = self.new(order_vals)
            new_sale.onchange_partner_id()
            order_vals = self._convert_to_write({name: new_sale[name] for name in new_sale._cache})
            new_sale = self.create(order_vals)
            #create sale order line
            for pos_line_vals in orderline:
                sale_line = new_sale._prepare_order_line(pos_line_vals)
                SaleOrderLines.create(sale_line)
            new_sale.compute_taxes()
            if self._context.get('confirm') or self._context.get('paid'):
                new_sale.action_confirm()
                if pos_config.stock_location_id:
                    for picking in new_sale.picking_ids:
                        picking.write({'location_id': pos_config.stock_location_id.id})
                        picking.move_lines.write({'location_id': pos_config.stock_location_id.id})
                        for move in picking.move_lines:
                            for move_line in move.move_line_ids:
                                move_line.write({'location_id': pos_config.stock_location_id.id})
            if self._context.get('paid'):
                inv_id = new_sale.action_invoice_create()
                if not self.generate_invoice(inv_id, journals):
                    return False
                if not self.delivery_order(new_sale):
                    return False
                new_sale.action_done()
            response_pos = new_sale._prepare_response_for_pos()
        return response_pos
    
    @api.model
    def generate_invoice(self, inv_id, journals):
        invoice = self.env['account.invoice'].browse(inv_id)
        if invoice:
            invoice.action_invoice_open()
            Payments = self.env['account.payment']
            for pos_payment_vals in journals:
                payment_vals = self._prepare_invoice_payment(invoice, pos_payment_vals)
                if payment_vals:
                    payment = Payments.create(payment_vals)
                    payment.post()
            return True
        return False

    def delivery_order(self, sale_order):
        for picking in sale_order.picking_ids:
            if picking.move_lines:
                picking.action_confirm()
                picking.action_assign()
                for move in picking.move_lines:
                    move.quantity_done = move.product_uom_qty
                picking.action_done()
        return True
