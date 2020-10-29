from odoo import fields, models, api


class ModelName (models.Model):
    _inherit = 'hr.contract'

    compensation_saving_id = fields.Many2one('hr.ccaf')

    saving_value = fields.Float()

    
