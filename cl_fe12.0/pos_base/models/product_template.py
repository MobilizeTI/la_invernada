from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    is_dummy_product = fields.Boolean("Hide Producto on POS?")