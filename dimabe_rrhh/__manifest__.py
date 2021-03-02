# -*- coding: utf-8 -*-
{
    'name': "Dimabe RRHH",

    'summary': """RRHH""",

    'description': """
        Módulo de recursos humanos Dimabe
    """,

    'author': "Dimabe ltda",
    'website': "http://www.dimabe.cl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','l10n_cl_hr','l10n_cl_hr_payroll_account','hr','hr_payroll'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'reports/remunerations_book.xml',
        'views/wizard_hr_payslip.xml',
        'views/custom_data.xml',
        'views/hr_contract.xml',
        'views/hr_department.xml',
        'views/hr_leave.xml',
        'views/custom_settlement.xml',
        'views/hr_payslip.xml',
        'views/custom_holidays.xml',
        'reports/settlement_document.xml',
        'reports/holiday_ticket.xml',
        'reports/hr_payslip_report.xml',
        'views/hr_payroll_structure.xml',
        'views/hr_salary_rule.xml',
        'views/hr_indicadores.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}