# Copyright 2013-17 Agile Business Group (<http://www.agilebg.com>)
# Copyright 2016 AvanzOSC (<http://www.avanzosc.es>)
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2017 Jacques-Etienne Baudoux <je@bcim.be>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Stock Picking Invoice Link Purchase',
    'version': '11.0.1.0.0',
    'category': 'Warehouse Management',
    'summary': 'Adds link between pickings and invoices from purchase order',
    'author': 'Agile Business Group, '
              'Tecnativa, '
              'BCIM sprl, '
              'Softdil S.L, '
              'Odoo Community Association (OCA)',
    'website': 'http://www.agilebg.com',
    'license': 'AGPL-3',
    'depends': [
        'purchase',
        'stock_account',
        'stock_picking_invoice_link',
    ],
    'data': [
    ],
    'installable': True,
    'auto_install': True,
}
