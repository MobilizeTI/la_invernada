
{
    'name': 'POS Base',
    'version': '1.0.0.0',
    'category': 'Point of Sale',
    'summary': """Modulo tecnico, sirve de base para otros modulos del POS""",
    'sequence': 5,
    'author': 'Flectra Chile SPA',
    'website': 'http://flectrachile.cl/',
    'depends': [
        'point_of_sale',
    ],
    'data': [
        'data/config_parameters_data.xml',
        'views/account_journal_view.xml',
        'views/product_template_view.xml',
        'views/pos_config_view.xml',
        'views/pos_assets.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml'
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
