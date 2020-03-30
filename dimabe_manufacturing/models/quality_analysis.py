from odoo import fields, models


class QualityAnalysis(models.Model):
    _inherit = 'quality.analysis'

    potential_client_id = fields.Many2one('res.partner', 'Posible Cliente')

    potential_workcenter_id = fields.Many2one('mrp.workcenter', 'Posible Proceso')

    lot_producer_id = fields.Many2one(
        'res.partner',
        related='stock_production_lot_ids.producer_id',
        string='Productor'
    )

    lot_product_variety = fields.Char(
        'Variedad',
        related='stock_production_lot_ids.product_variety'
    )

    process_observation = fields.Text('Observación para proceso')
