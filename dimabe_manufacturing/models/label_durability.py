from odoo import fields, models, api


class LabelDurability(models.Model):
    _name = 'label.durability'
    _description = 'duración de la etiqueta en meses'
    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'esta cantidad de meses ya existe en el sistema')
    ]

    _order = 'name'

    name = fields.Char(
        'Duración',
        compute='_compute_name',
        inverse='_inverse_name',
        store=True
    )

    month_qty = fields.Integer(
        'Meses',
        required=True,
    )

    @api.depends('month_qty')
    @api.multi
    def _compute_name(self):
        for item in self:
            item.name = item.month_qty

    @api.multi
    def _inverse_name(self):
        for item in self:
            item.month_qty = item.name
