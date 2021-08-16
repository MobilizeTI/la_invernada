{
    "name": "Roles de usuario",
    "version": "1.0",
    "depends": [
        'base',
    ],
    "author": "Carlos López Mite",
    "website": "",
    "category": "Tools",
    "complexity": "normal",
    "description": """
    This module provide :
    Roles para asignar a usuarios, simplicidad en permisos de acceso
    """,
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/res_group_rol_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
