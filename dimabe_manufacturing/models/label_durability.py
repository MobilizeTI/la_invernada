from odoo import fields, models


class LabelDurability(models.Model):
    _name = 'label.durability'
    _description = 'duración de la etiqueta en meses'
    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'esta cantidad de meses ya existe en el sistema')
    ]

    name = fields.Integer(
        'Duración',
        required=True
    )
