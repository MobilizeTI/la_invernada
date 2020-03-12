from odoo import fields,models,api

class ProductTemplate(models.Models):
    _inherit = 'product.template'

    is_standard_weight = fields.Boolean('Peso Estandar',default=False)