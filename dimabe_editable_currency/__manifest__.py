# -*- coding: utf-8 -*-
{
    'name': "dimabe editable currency",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

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
    'depends': [
        'base',
        'account_accountant'
    ],

    # always loaded
    'data': [
        'data/currency_update_cron.xml',
        'security/ir.model.access.csv',
        'views/account_invoice.xml',
        'views/account_payment.xml',
        'views/templates.xml',
        'views/balance_sheet_clp.xml',
        'views/account_move.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml'
    ],
    'qweb': [
        "static/src/xml/button_get_data.xml",
    ],
}