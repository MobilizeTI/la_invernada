from odoo import models, api, fields, tools
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class PickingNoDoneOnDate(models.AbstractModel):
    _inherit = 'mail.template.parser'
    _name = 'mail.view_et_picking_no_done_on_date.parser'
    
    @api.model
    def get_values(self, template, record):
        values = super(PickingNoDoneOnDate, self).get_values(template, record)
        picking_model = self.env['stock.picking']
        picking_to_sent_ids = self.env.context.get('picking_to_sent_ids')
        if not picking_to_sent_ids:
            picking_to_sent = picking_model._get_picking_no_done()
        else:
            picking_to_sent = picking_model.browse(picking_to_sent_ids)
        values['picking_to_sent'] = picking_to_sent
        return values
