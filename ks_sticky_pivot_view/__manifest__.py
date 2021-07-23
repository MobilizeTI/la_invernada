# -*- coding: utf-8 -*-
{
    'name': "Sticky Pivot View",

    'summary': """
        Enhance the default Odoo Pivot View by sticking the Pivot View Header and its first Column.""",

    'description': """
        Enhance the default Odoo Pivot View by sticking the Pivot View Header and its first Column.
        Pivot View
        Sticky Pivot View
        Odoo Sticky Pivot View
        Odoo Pivot View 
        Web List View Sticky Header 
        Odoo Sticky Header 
        Pivot View Sticky Header 
        Sticky Header 
        Sticky Pivot View Header 
        Sticky Pivot View Column 
        Freeze Pivot View

    """,


    'author': "Ksolves",
    'website': "https://www.ksolves.com/",
    'support': "sales@ksolves.com",
    'license': 'LGPL-3',
    'category': 'Tools',
    'version': '1.0.0',
    'images': ['static/description/main.jpg'],
    'depends': ['base','web','base_setup'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/data_ir_config_parameter.xml',
        'views/ks_assets.xml',
        'views/ks_inherited_res_config.xml',
    ],
    # 'qweb': [
    #     '/static/xml/inherited_pivot.xml'
    # ]
}
