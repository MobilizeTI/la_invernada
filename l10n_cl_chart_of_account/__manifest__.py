# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (c) 2021 Mobilize SPA (https://www.mobilize.cl/)

{
    'name': 'Chile Localization Chart Account SII',
    'version': '1.10.0',
    'description': """
Chilean accounting chart and tax localization.
==============================================
Plan contable chileno e impuestos de acuerdo a disposiciones vigentes,
basado en plan de cuentas del Servicio de Impuestos Internos

    """,
    'author': 'Mobilize SPA',
    'website': 'https://www.mobilize.cl/',
    'category': 'Localization',
    'sequence': 50,
    'license': 'AGPL-3',
    'depends': ['account'],
    'data': [
        'views/account_tax.xml',
        'data/product_uom.xml',
        'data/l10n_cl_chart_of_account_data.xml',
        'data/account_tax_data.xml',
        'data/account_chart_template_data.xml',
        'data/account_journal.xml',
    ],
    'installable': True,
}
