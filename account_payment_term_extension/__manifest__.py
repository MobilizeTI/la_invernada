Mobilize SPA Copyright 2013-2016 Camptocamp SA (Yannick Vaucher)
# Copyright 2015-2016 Akretion
# (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Payment Term Extension',
    'version': '11.0.1.0.0',
    'category': 'Accounting & Finance',
    'summary': 'Adds rounding, months, weeks and multiple payment days '
               'properties on payment term lines',
    'author': 'Mobilize SPA',
    'maintainer': 'Mobilize SPA',
    'website': 'https://www.mobilize.cl/',
    'license': 'AGPL-3',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_payment_term.xml'],
    'demo': ['demo/account_demo.xml'],
    'installable': True,
}
