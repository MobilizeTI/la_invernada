from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _

CHANNEL = "stock_transfers"


class PosConfig(models.Model):
    _inherit = 'pos.config'
    
    allow_sent_internal_transfers = fields.Boolean('Generar transferencias internas?', default=False)
    allow_received_internal_transfers = fields.Boolean('Recibir transferencias internas?', default=False)
    
    @api.model
    def notify_transfer_updates(self):
        message = {}
        self.search([])._send_to_channel(CHANNEL, message)
