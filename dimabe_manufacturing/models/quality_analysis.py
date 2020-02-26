from odoo import fields, models


class QualityAnalysis(models.Model):
    _inherit = 'quality.analysis'

    potential_client_id = fields.Many2one('res.partner', 'Posible Cliente')

    potential_workcenter_id = fields.Many2one('mrp.workcenter', 'Posible Proceso')
