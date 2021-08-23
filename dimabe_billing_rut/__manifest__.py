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
    'depends': ['base', 'stock', 'account', 'hr_payroll',
                'hr_payroll_account','sale','product','uom','account_accountant'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'data/dte.type.csv',
        # 'data/custom.economic.activity.csv',
        'views/res_company.xml',
        'views/res_partner.xml',
        'views/account_invoice.xml',
        'views/stock_picking.xml',
        'views/stock_location.xml',
        'views/custom_economic_activity.xml',
        'views/dte_type.xml',
        'views/templates.xml',
        'views/custom_invoice.xml',
        'data/reports/balance_sheet_clp.xml',
        'views/wizard_account_move.xml',
        'views/custom_export_clause.xml',
        'views/custom_sale_method.xml',
        'views/custom_type_transport.xml',
        'views/custom_receiving_country_dte.xml',
        'views/custom_package_type.xml',
        'views/custom_uom.xml',
        'views/res_country.xml',
        'views/res_currency.xml',
        'views/account_incoterms.xml',
        'views/account_move.xml',
        'report/instructive_report.xml',
        'report/report_pdf.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'qweb': [
        "static/src/xml/custom_invoice_button.xml",
        "static/src/xml/action_manager.xml"
    ],
}
