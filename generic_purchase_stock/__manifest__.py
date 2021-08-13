{
    "name": "Mejoras en Proceso de Compras-Stock",
    'version': '1.0.0.0',
    "author": "Carlos Lopez Mite",
    "website": "https://blaze-otp.com",
    'category': 'Purchases',
    "description": """Mejoras en Proceso de Compras-Stock""",
    'depends': [
        'purchase',
        'purchase_stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_report_view.xml',
        'views/purchase_view.xml',
        'views/report_purchase_stock_view.xml',
    ],
    'installable': True,
    'auto_install': True,
}
