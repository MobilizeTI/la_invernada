# -*- coding: utf-8 -*-

from odoo import fields, models, api
import odoo.addons.decimal_precision as dp
 

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _total_discount(self):
        for rec in self:
            discount_amount = 0
            for line in rec.order_line:
                discount_amount += line.discount_amount
            rec.discount_amount = discount_amount
            rec.avg_discount = (discount_amount*100)/rec.amount_untaxed if rec.amount_untaxed else 0


    discount_amount = fields.Float('Total Disocunt', compute="_total_discount", digits=dp.get_precision('Discount'))
    avg_discount = fields.Float('Avg Disocunt', compute="_total_discount", digits=dp.get_precision('Discount'))
    print_discount = fields.Boolean('Print Discount')
    print_discount_amount = fields.Boolean('Print Discount Amount')


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _total_discount(self):
        for rec in self:
            discount = ((rec.discount*rec.price_unit)/100)
            rec.discount_per_unit = discount
            rec.discount_amount = discount*rec.product_qty
            rec.discounted_unit_price = rec.price_unit - discount

    discount_amount = fields.Float('Discount Amount', compute="_total_discount", digits=dp.get_precision('Discount'))
    discount_per_unit = fields.Float('Discount Per Unit', compute="_total_discount", digits=dp.get_precision('Discount'))
    multi_discount = fields.Char('Discounts')
    discounted_unit_price = fields.Float('Discounted Unit Price', compute="_total_discount", digits=dp.get_precision('Discount'))


    @api.onchange('multi_discount')
    def _onchange_multi_discount(self):
        def get_disocunt(percentage,amount):
            new_amount = (percentage * amount)/100
            return (amount - new_amount)
        if self.multi_discount:
            amount = 100
            splited_discounts = self.multi_discount.split("+")
            for disocunt in splited_discounts:
                amount = get_disocunt(float(disocunt),amount)
            self.discount = 100 - amount
        else:
            self.discount = 0

