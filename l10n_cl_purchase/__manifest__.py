{
    'name': 'Personalizacion Chilena en Compras',
    'version': '1.0.0.0',
    'category': 'Purchases',
    'description': """""",
    'author': 'Mobilize SPA',
    'depends': [
        'account',
        'product',
        'purchase',
        'generic_purchase',
        'stock',
        'stock_account',
        'l10n_cl_fe',
        'l10n_cl_base',
        'account_analytic_default_warehouse',
        'dusal_purchase',
        'purchase_picking_state',
        'purchase_stock_picking_return_invoicing',
    ],
    'data': [
        'views/purchase_report_view.xml',
        'views/purchase_view.xml',
        'report/purchase_report.xml',
        'report/purchase_quotation_report.xml',
    ],
    'installable': True,
}
