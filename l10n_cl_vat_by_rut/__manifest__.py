{
    'name': 'Cambiar VAT por RUT en reportes',
    'version': '0.0.0.1',
    'category': 'Tools',
    'description': "",
    'author': 'Mobilize SPA',
    'depends': [
        'l10n_cl_fe',
        'sale',
        'web',
    ],
    'data': [
        'data/res_country_data.xml',
        'report/report_layout_templates.xml',
        'report/sale_report_templates.xml',
    ],
    'installable': True,
}
