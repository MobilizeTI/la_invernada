{
    'name': 'POS Pricelist',
    'version': '1.0.0.0',
    'category': 'Point Of Sale',
    'author': "Carlos Lopez Mite",
    'summary': 'Show discount visible on pos',
    'description': """
Show discount visible on pos:
=============================
    """,
    'depends': [
        "point_of_sale",
        "sale",
    ],
    'data': [
        "views/pos_pricelist_template.xml",
    ],
    'qweb': [
        'static/src/xml/pos_view.xml',
    ],
    'installable': True,
}
