from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    mail_layout_view_id = fields.Many2one(
        'ir.ui.view', 'Default Notify Layout', 
        domain=[('type', '=', 'qweb'), ('name', 'ilike', 'mail_notification')])
    force_notify_layout = fields.Boolean(u'Force use Notify layout?')
