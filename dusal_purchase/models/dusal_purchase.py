# -*- coding: utf-8 -*-
##############################################################################
#
#    Addon for Odoo Purchase by Dusal.net
#    Copyright (C) 2015 Dusal.net Almas
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from odoo import models, fields, osv

class purchase_order(models.Model):
    _name = 'purchase.order'
    _inherit = 'purchase.order'
    

    print_image = fields.Boolean('Print image', readonly=False, index=True, help="Print Quotation with product images", default=True)
    image_size = fields.Selection([('small', 'Small'), ('medium', 'Medium'), ('original', 'Big')], 'Image sizes', help="Choose an image size here", index=True, default='small')
    print_line_number = fields.Boolean('Print line number', readonly=False, index=True, help="Print line number on Sales order & Quotation", default=False)
    
class purchase_order_line(models.Model):
    _name = 'purchase.order.line'
    _inherit = 'purchase.order.line'

    product_image = fields.Binary(string="Image", related="product_id.image")
    product_image_medium = fields.Binary(string="Image small", related="product_id.image_medium")
    product_image_small = fields.Binary(string="Image medium", related="product_id.image_small")
