from odoo import models, fields, api


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    show_in_book = fields.Boolean('Aparece en el libro de remuneraciones', default=True)

    order_number = fields.Integer('Orden')

    show_in_central = fields.Boolean('Aparece en Centralizacion')

    is_legal = fields.Boolean('Es un descuento Legal')

