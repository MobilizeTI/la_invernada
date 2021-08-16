{
    'name': 'POS Payment Ref',
    'version': '12.0.0.0.0',
    'category': 'Point of Sale',
    'summary': """Permite pedir un codigo de autorizacion del pago(pagos tipo banco)""",
    'sequence': 5,
    'author': 'Flectra Chile SPA',
    'website': 'http://flectrachile.cl/',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_payment_ref.xml',
        'views/account_journal_view.xml',
        'views/account_bank_statement_line_view.xml',
        'views/pos_order_view.xml',
    ],
    'excludes': [
        'pos_payment_code',
    ],
    'images': ['static/description/log_img.png'],
    'installable': True,
    'application': True,
    'qweb': ['static/src/xml/pos_payment_ref.xml'],
}
