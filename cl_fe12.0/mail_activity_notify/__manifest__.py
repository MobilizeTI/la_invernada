{
    'name': 'Notificacion por correo de actividades',
    'version': '1.0.0.0',
    'category': 'Discuss',
    'description': """""",
    'author': 'Carlos Lopez Mite(celm1990@hotmail.com)',
    'depends': ['base',
                'mail',
                'web',
                'email_template_qweb',
                ],
    'data': [
        'data/mail_template_view.xml',
        'data/mail_template.xml',
        'data/cron_jobs_data.xml',
    ],
    'installable': True,
    'auto_install': False,
}
