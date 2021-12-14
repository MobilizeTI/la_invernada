# -*- coding: utf-8 -*-
{
    "name": "Stock Movimientos Inter-Compañía",
    "version": "14",
    "author": "Mobilize (Jorge Quico)",
    'category': 'Mobilize/Apps',
    "application": True,
    "depends": [ "base", "stock" ],
    "data": [
        #"security/ir.model.access.csv",
        "data/stock_quant.xml",
        "views/stock_location.xml",
        "views/stock_picking_type.xml",
        "views/stock_picking.xml",
    ],
    "summary": "Permite realizar movimientos y consulta de stock entre compañías",
    "description": """
        Permite realizar movimientos y consulta de stock entre compañías
    """
}
