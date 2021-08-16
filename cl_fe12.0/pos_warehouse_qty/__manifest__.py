# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2013-Present Acespritech Solutions Pvt. Ltd. (<http://acespritech.com>).
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

{
    'name': 'POS Warehouse Quantity',
    'version': '1.0',
    'category': 'Point of Sale',
    'summary': 'This module allow user to show product quantity from warehouse',
    'description': """
This module allow user to check product quantity in different warehouse from Point of Sale.
""",
    'author': 'Acespritech Solutions Pvt. Ltd.',
    'website': 'http://www.acespritech.com',
    'price': 25,
    'currency': 'EUR',
    'depends': [
        'base', 
        'point_of_sale',
        'pos_base',
    ],
    'images': ['static/description/main_screenshot.png'],
    "data": [
        'views/pos_warehouse_qty.xml',
    ],
    'qweb': [
            'static/src/xml/pos.xml'
    ],
    'installable': True,
    'auto_install': False,
}
