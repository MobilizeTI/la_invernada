from odoo import models, fields , api

class CustomParameter(models.Models):
    _name = 'custom.paramenter'


    name  = fields.Char('Nombre')

    value = fields.Char('Valor')

    comment  = fields.Char('Comentario')


    