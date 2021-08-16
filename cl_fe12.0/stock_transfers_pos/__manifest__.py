
{
"name" : "Transferencias internas desde POS",
"version" : "1.0",
"author" : "Carlos López Mite",
"website" : "http://www.blaze-otp.com",
"category" : "Inventory",
"depends" : [
    'base',
    'product',
    'stock',
    'stock_account',
    'odoo_utils',
    'generic_stock',
    'stock_transfers',
    'pos_longpolling',
    'point_of_sale',
    'pos_stock_quantity',
    'pos_base',
],
"description": """Standard Process""",
"data": [
    'views/pos_config_view.xml',
    'views/stock_transfers_pos_assets.xml',
    'security/ir.model.access.csv',
],
'qweb': [
    'static/src/xml/pos.xml',
],
"installable": True,
"auto_install": True,
}
