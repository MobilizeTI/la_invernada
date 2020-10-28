from odoo import http,models,fields

class HrContract(models.Models):
    _inherit = 'hr.contract'

    compensation_saving_id = fields.Many2one('hr.ccaf','Caja de Compensacion')

    saving_value = fields.Float('Valor de Ahorro')