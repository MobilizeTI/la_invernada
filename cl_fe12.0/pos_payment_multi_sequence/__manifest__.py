{
    'name': "Manejar secuencias diferentes por TPV para pagos",
    'version': '1.0.0.0',
    "author" : "Carlos López Mite",
    "website": "https://blaze-otp.com",
    'category': 'Point Of Sale',
    'description': """
        Este modulo permite configurar una secuencia diferente para cada TPV en los diarios de pago
        y asi evitar el error de concurrencia cuando un mismo diario se comparta entre varios TPV(al cerrar session)
    """,
    'depends': [
        'account',
        'point_of_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_journal_view.xml',
        'views/pos_config_view.xml',
    ],
    'installable': True,
    'auto_install': True,
}
