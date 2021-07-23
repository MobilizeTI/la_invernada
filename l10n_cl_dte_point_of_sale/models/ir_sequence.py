from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class IrSequence(models.Model):
    _inherit = 'ir.sequence'
    
    show_in_pos = fields.Boolean('Permitir seleccionar en POS?', default=False)
    mode_online = fields.Boolean('Ventas en modo On-line?')
    correct_folios_automatic = fields.Boolean('Corregir Folios automaticamente?')
