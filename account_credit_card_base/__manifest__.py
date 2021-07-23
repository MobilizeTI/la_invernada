{
    "name" : "Base para usar Tarjetas de Credito",
    'version': '1.0.0.0',
    "author" : "MOBILIZE SPA",
    "website": "https://mobilize.cl",
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
