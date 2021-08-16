{
    'name': 'Mejoras en Proceso de Ventas-Stock',
    'version': '1.0.0.0',
    'category': 'Sales',
    'description': """Mejoras en Proceso de Ventas-Stock""",
    'author': 'Carlos Lopez Mite(celm1990@hotmail.com)',
    'depends': [
        'sale',
        'sales_team',
        'sale_stock',
        'generic_account',
        'generic_stock',
        'stock_picking_invoice_link',
    ],
    'data': [
        'views/product_template_view.xml',
        'views/sale_order_view.xml',
    ],
    'installable': True,
    'auto_install': True,
}
