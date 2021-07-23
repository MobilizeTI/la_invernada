# -*- coding: utf-8 -*-
{
    "name": """Boleta / Factura Electrónica Chilena para punto de ventas \
    """,
    'version': '0.21.10',
    'category': 'Point of Sale/Localization/Chile',
    'sequence': 12,
    'author':  'Mobilize SPA',
    'website': 'https://www.mobilize.cl/',
    'license': 'AGPL-3',
    'summary': '',
    'description': """
Chile: API and GUI to access Electronic Invoicing webservices for Point of Sale.
""",
    'depends': [
        'l10n_cl_fe',
        'account',
        'point_of_sale',
        'portal',
        'odoo_utils',
        'pos_pricelist',
        'pos_payment_ref',
        'pos_orders_history',
        'pos_orders_history_reprint',
        ],
    'external_dependencies': {
        'python': [
        ]
    },
    'data': [
        'data/cron_jobs.xml',
        'report/report_pos_common_templates.xml',
        'report/report_pos_boleta.xml',
        'wizard/notas.xml',
        'wizard/wizard_change_journal_pos_order_view.xml',
        'wizard/journal_config_wizard_view.xml',
        'views/ir_sequence_view.xml',
        'views/pos_dte.xml',
        'views/pos_config.xml',
        'views/pos_session.xml',
        'views/point_of_sale.xml',
        'views/portal_boleta_layout.xml',
        'views/res_company_view.xml',
        'views/sii_xml_envio.xml',
        'wizard/masive_send_dte.xml',
#        'data/sequence.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [
        'static/src/xml/buttons.xml',
        'static/src/xml/pos.xml',
        'static/src/xml/layout.xml',
        'static/src/xml/client.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
