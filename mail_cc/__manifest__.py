{
    'name': 'Cc y Cco en mails',
    'version': '1.0.0.0',
    'category': 'Discuss',
    'description': """
""",
    'author': 'Carlos Lopez Mite(celm1990@hotmail.com)',
    'depends': [
        'base',
        'mail',
        'web',
    ],
    'data': [
        'data/config_parameters_data.xml',
        'wizard/wizard_select_email_view.xml',
        'wizard/mail_compose_message_view.xml',
        'views/mail_template_view.xml',
        'views/mail_message_view.xml',
        'views/mail_mail_view.xml',
    ],
    'installable': True,
    'auto_install': True,
}
