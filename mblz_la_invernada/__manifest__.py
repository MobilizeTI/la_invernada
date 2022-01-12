{
    'name': 'Customizacion La Invernada',
    'version': '1.0.0.0',
    'category': 'Personalization',
    'description': """
""",
    'author': 'Felipe Angulo, Mobilize SPA',

    'depends': [
        'l10n_cl_fe',

        'account'

    ],

    'data': [
        'security/ir.model.access.csv',
        'views/report_views.xml',
        'wizard/wizard_diary_account_move_line_report.xml',

        'views/mail_message_dte_document.xml',
        'report/mail_message_dte_document.xml',

    ],

    'installable': True,
    "images": ['static/description/icon.png'],
}
