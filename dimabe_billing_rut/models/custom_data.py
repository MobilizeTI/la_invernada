from odoo import models, fields


class CustomData(models.Models):
    _name = 'custom.data'

    name = fields.Char('Nombre')

    value = fields.Char('Valor')

    comment = fields.Char('Comentario')
