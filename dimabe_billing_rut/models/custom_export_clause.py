from odoo import models, fields, api

class CustomExportClause(models.Model):

    _name = 'custom.export.clause'
    _rec_name = 'initials'

    name = fields.Char(string= 'Nombre', required=True)

    initials = fields.Char(string= 'Sigla', required=True)

    code = fields.Char(string= 'Código', required=True)

