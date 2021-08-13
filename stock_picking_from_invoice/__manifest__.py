
{
    "name" : "Crear Picking desde Facturas",
    'version': '1.0.0.0',
    "author" : "Carlos López Mite",
    "website": "https://blaze-otp.com",
    "category" : "Warehouse",
    "description": """Este modulo permite crear picking desde facturas""",
    "depends" : [
        'base',
        'product',
        'account',
        'stock',
        'stock_account',
        'stock_picking_invoice_link', #OCA dependency
    ],
    "data": [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/account_invoice_view.xml',
    ],
    "installable": True,
}
