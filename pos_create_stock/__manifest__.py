{
    'name': 'Crear Picking desde POS',
    'version': '0.0.0.1',
    'category': 'Warehouse',
    'description': """
""",
    'author': 'Carlos Lopez Mite(celm1990@hotmail.com)',
    'depends': [
        'stock',
        'point_of_sale',
        'pos_longpolling',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_config_view.xml',
        'views/pos_create_stock_assets.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ],
    'installable': True,
}
