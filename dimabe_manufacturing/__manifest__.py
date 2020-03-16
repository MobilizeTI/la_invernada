# -*- coding: utf-8 -*-
{
    'name': "Fabricación Dimabe",

    'summary': """
        Módulo que modifica la fabricación actual y la adapta a la realidad de productos frutícolas.
        """,

    'description': "",

    'author': "Dimabe ltda",
    'website': "http://www.dimabe.cl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'web',
        'dimabe_reception',
        'mrp',
        'mrp_workorder',
        'dimabe_export_order',
        'dimabe_quality_integration'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_workorder.xml',
        'views/stock_production_lot_serial.xml',
        'views/stock_production_lot.xml',
        'views/mrp_production.xml',
        'reports/lot_serial_label_report.xml',
        'views/views.xml',
        'views/mrp_dispatched.xml',
        'views/mrp_workcenter.xml',
        'views/quality_analysis.xml',
        'views/product_category.xml',
        'views/potential_lot.xml',
        'views/templates.xml',
        'views/stock_picking.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
