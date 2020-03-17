from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    always_to_print = fields.Boolean('Mostrar Siempre en Impresión se Etiquetas')
