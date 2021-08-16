# -*- encoding: utf-8 -*-
##############################################################################
#    Copyright (c) 2012 - Present Acespritech Solutions Pvt. Ltd. All Rights Reserved
#    Author: <info@acespritech.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of the GNU General Public License is available at:
#    <http://www.gnu.org/licenses/gpl.html>.
#
##############################################################################

from odoo import models, fields, api, _
from odoo.tools.float_utils import float_is_zero


class stock_warehouse(models.Model):
    _inherit = 'stock.warehouse'

    @api.model  
    def disp_prod_stock(self, product_id):
        stock_line = []
        total_qty = 0
        ctx = self.env.context.copy()
        product = self.env['product.product'].browse(product_id)
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for warehouse in self.sudo().search([('company_id', '=', self.env.user.company_id.id)], order="name"):
            ctx['location'] = warehouse.lot_stock_id.id
            ctx['show_all_stock'] = True
            qty_available = product.with_context(ctx)._compute_quantities_dict(ctx.get('lot_id'), ctx.get('owner_id'), ctx.get('package_id'), ctx.get('from_date'), ctx.get('to_date'))[product.id]['qty_available']
            if float_is_zero(qty_available, precision_digits=precision):
                continue
            stock_line.append([warehouse.name, qty_available])
            total_qty += qty_available
        return stock_line, total_qty
