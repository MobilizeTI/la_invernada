from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _

CHANNEL = "stock_adjustment"


class PosConfig(models.Model):
    _inherit = 'pos.config'
    
    allow_delivery_note = fields.Boolean('Permitir crear Guias?', default=False)
    allow_inventory_adjust = fields.Boolean('Permitir crear Ajustes de inventario?', default=False)

    @api.model
    def notify_adjustment_updates(self):
        message = {}
        self.search([])._send_to_channel(CHANNEL, message)