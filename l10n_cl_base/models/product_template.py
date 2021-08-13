from odoo import models, api, fields, tools


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    @api.depends('product_variant_ids', 'product_variant_ids.default_code')
    def _compute_default_code(self):
        unique_variants = self.filtered(lambda template: len(set(template.product_variant_ids.mapped('default_code'))) == 1)
        for template in unique_variants:
            template.default_code = template.product_variant_ids[0].default_code
        for template in (self - unique_variants):
            template.default_code = ''
            
    @api.one
    def _set_default_code(self):
        if len(set(self.product_variant_ids.mapped('default_code'))) == 1:
            self.product_variant_ids.write({'default_code': self.default_code})
