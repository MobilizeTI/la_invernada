from odoo import fields, models, api


class ModelName(models.Model):
    _inherit = 'hr.leave.type'

    unpaid = fields.Boolean('Es no Pagada?', required=True)

    validaty_start = fields.Date('Fecha de inicio',required=True)