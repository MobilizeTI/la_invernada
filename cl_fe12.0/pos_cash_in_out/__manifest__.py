{
    'name': 'POS Ingresar/Sacar Dinero',
    'version': '0.0.0.0',
    'category': 'Point of Sale',
    'description': """
Permitir Ingresar/Sacar Dinero desde el TPV
=========================================== 
""",
    'author': 'Carlos Lopez Mite(celm1990@hotmail.com)',
    'depends': ['base',
                'web',
                'point_of_sale',
                'pos_base',
                ],
    'data': [
        'views/pos_session_view.xml',
        'views/pos_config_view.xml',
        'views/pos_cash_in_out_assets.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml'
    ],
    'installable': True,
}
