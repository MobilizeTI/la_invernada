# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
    'name': "Integración Calidad Dimabe",

    'summary': """
        Establece comunicación entre sistema de calidad DIMABE y ODOO""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Dimabe ltda.",
    'website': "http://www.dimabe.cl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'mrp',
        'stock',
        'dimabe_jwt_token',
        'dimabe_reception'
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking.xml',
        'views/caliber_analysis.xml',
        'views/external_damage_analysis.xml',
        'views/internal_damage_analysis.xml',
        'views/performance_analysis.xml',
        'views/color_analysis.xml',
        'views/form_analysis.xml',
        'views/impurity_analysis.xml',
        'views/quality_analysis.xml',
        'views/humidity_analysis.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}