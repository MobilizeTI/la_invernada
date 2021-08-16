{
    'name': 'TPV por usuarios',
    'version': '1.0.0.0',
    'category': 'Point of Sale',
    'summary': """Permitir acceso a usuarios solo en los TPV configurados para cada usuario(escenario multi tiendas)""",
    'sequence': 5,
    'author': 'Flectra Chile SPA',
    'website': 'http://flectrachile.cl/',
    'depends': [
        'base',
        'mail',
        'web',
        'product',
        'point_of_sale',
    ],
    'data': [
        'security/rule_security.xml',
        'views/res_users_view.xml',
        'views/pos_config_view.xml',
        'views/assets.xml',
    ],
    'installable': True,
    'application': True,
}
