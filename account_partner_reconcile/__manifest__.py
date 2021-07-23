# Copyright 2017-19 Eficent Business and IT Consulting Services S.L.
#        (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': "Account Partner Reconcile",
    'version': '12.0.1.0.1',
    'category': 'Accounting',
    'author': 'Mobilize SPA',
    'website': 'https://mobilize.cl',
    'license': 'AGPL-3',
    "depends": [
        'account',
    ],
    "data": [
        'views/res_partner_view.xml',
    ],
    "installable": True
}
