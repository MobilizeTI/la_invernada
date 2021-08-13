from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class ResConfig(models.TransientModel):
    _inherit = 'res.config.settings'
    
    mail_layout_view_id = fields.Many2one(
        'ir.ui.view', 'Default Notify Layout', 
        related="company_id.mail_layout_view_id", readonly=False)
    force_notify_layout = fields.Boolean(u'Force use Notify layout?',
        related="company_id.force_notify_layout", readonly=False)
