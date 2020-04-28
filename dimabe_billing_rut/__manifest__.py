# -*- coding: utf-8 -*-
{
    'name': "Documentos Tributarios Electrónicos",

    'summary': """
        Agrega campo rut de facturación y validación de este, además contempla conector con facturador electrónico""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Dimabe ltda",
    'website': "http://www.dimabe.cl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock','account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/dte.type.csv',
        'views/res_company.xml',
        'views/dte_type.xml',
        'views/res_partner.xml',
        'views/account_invoice.xml',
        'views/stock_location.xml',
        'views/custom_economic_activity.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}