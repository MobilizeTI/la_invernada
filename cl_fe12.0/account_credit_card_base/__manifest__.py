{
    "name" : "Base para usar Tarjetas de Credito",
    'version': '1.0.0.0',
    "author" : "Carlos López Mite",
    "website": "https://blaze-otp.com",
    "category" : "Accounting",
    "depends" : [
        'account',
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/account_journal_view.xml',
        'views/credit_card_provider_view.xml',
    ],
    "auto_install": False,
    "installable": True,
}
