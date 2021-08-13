from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class PosConfig(models.Model):
    _inherit = 'pos.config'
    
    user_ids = fields.Many2many('res.users', 'pos_config_users_rel', 
        'config_id', 'user_id', 'Usuarios')
