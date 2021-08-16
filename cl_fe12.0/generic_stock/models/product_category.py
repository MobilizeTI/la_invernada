from odoo import models, api, fields
from odoo.exceptions import UserError, ValidationError


class ProductCategory(models.Model):
    _inherit = ['product.category', 'translations.unique']
    _name = 'product.category'
    _check_translations = True
    
    @api.model
    def action_translate_terms(self):
        ctx = self.env.context.copy()
        if not ctx.get('lang', ""):
            ctx = self.env['res.users'].context_get()
        categories = self.env.ref('product.product_category_all', False)
        categories |= self.env.ref('product.product_category_1', False)
        categories |= self.env.ref('product.cat_expense', False)
        for category in categories.with_context(ctx):
            category.write({'name': category.name})
        return True
