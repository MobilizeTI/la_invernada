# -*- coding: utf-8 -*-
{   'active': True,
    'author': 'Daniel Santibáñez Polanco, Cooperativa OdooCoop',
    'website': 'http://globalresponse.cl',
    'category': 'Stock',
    'depends': [
        'stock',
        'delivery',
        'sale_stock',
        'l10n_cl_fe',
        ],
    'description': '''
\n\nMódulo de Guías de Despacho de la localización Chilena.\n\n\nIncluye:\n
- Configuración de libros, diarios (journals) y otros detalles para Guías de despacho en Chile.\n
- Asistente para configurar los talonarios de facturas, boletas, guías de despacho, etc.
''',
    'init_xml': [],
    'installable': True,
    'license': 'AGPL-3',
    'name': 'Guías de Despacho Electrónica para Chile',
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking.xml',
        'views/stock_location.xml',
        'views/layout.xml',
        'views/libro_guias.xml',
        "views/account_invoice.xml",
        'wizard/masive_send_dte.xml',
    ],
    'application': True,
}
