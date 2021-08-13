{
    'name': 'Personalizacion Chilena',
    'version': '1.0.0.0',
    'category': 'Personalization',
    'description': """
""",
    'author': 'Carlos Lopez Mite(celm1990@hotmail.com)',
    'depends': [
        'base',
        'mail',
        'web',
        'product',
        'stock',
        'stock_account',
        'l10n_cl_fe',
        'mail_cc',
        'email_template_qweb',
        'odoo_utils',
    ],
    'data': [
        'data/company_data.xml',
        'data/res_country_data.xml',
        'data/stock_account_data.xml',
        'data/system_data_init.xml',
        'views/report_layout_templates.xml',
        'views/sii_document_class_view.xml',
    ],
    'installable': True,
}
