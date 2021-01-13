from odoo import models, fields, api


class HrSalaryRuleCategory(models.Model):
    _inherit = 'hr.salary.rule.category'

    order_from_book = fields.Integer('Orden')
