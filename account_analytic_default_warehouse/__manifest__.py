{
    'name': 'Cuentas analiticas por defecto por almacen',
    'version': '1.0.0.0',
    'category': 'Accounting',
    'description': """
Configurar valores por defecto para las cuentas analiticas.
============================================================

Agrega soporte para seleccionar cuentas analiticas basada en almacenes:
------------------------------------------------------------------------
    """,
    'author': 'Mobilize SPA',
    'depends': [
        'stock',
        'account_analytic_default',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_analytic_default_view.xml',
    ],
    'installable': True,
}
