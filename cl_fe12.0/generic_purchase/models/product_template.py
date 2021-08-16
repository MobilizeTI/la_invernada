from odoo import models, api, fields, tools


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    @api.model
    def get_groups_see_cost_product(self):
        return super(ProductTemplate, self).get_groups_see_cost_product() + ['purchase.group_purchase_manager']
