from odoo import fields, models, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    variety = fields.Char(
        'Variedad',
        compute='_compute_variety',
        search='_search_variety'
    )

    @api.multi
    def _compute_variety(self):
        for item in self:
            item.variety = item.get_variety()

    @api.multi
    def _search_variety(self, operator, value):
        attribute_value_ids = self.env['product.attribute.value'].search([('name', operator, value)])
        product_ids = []
        if attribute_value_ids:
            product_ids = self.env['product.product'].search([
                ('attribute_value_ids', '=', attribute_value_ids.mapped('id'))
            ]).mapped('id')

        return [('id', 'in', product_ids)]
