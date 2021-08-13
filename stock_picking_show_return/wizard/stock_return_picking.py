from odoo import models, api, fields

class StockReturnPicking(models.TransientModel):

    _inherit = 'stock.return.picking'
    
    def _prepare_picking_default_values(self, picking_type_id):
        vals = super(StockReturnPicking, self)._prepare_picking_default_values(picking_type_id)
        vals.update({
            'original_picking_id': self.picking_id.id,
            'devolution': True,
            'scheduled_date': fields.Datetime.now(),
        })
        return vals
