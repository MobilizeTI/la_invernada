from odoo import models, fields, api


class HrSalaryRuleCategory(models.Model):
    _inherit = 'hr.salary.rule.category'

    is_legal = fields.Boolean('Es Descuento legal')
