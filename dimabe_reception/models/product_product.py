from odoo import models, api, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    short_name = fields.Char(
        'Nombre Corto',
        compute='_compute_short_name'
    )

    @api.one
    def _compute_short_name(self):
        if self.name:
            self.short_name = self.name[0:25]

    @api.model
    def get_variety(self):
        return self.get_variant('variedad')

    @api.model
    def get_caliber(self):
        return self.get_variant('calibre')

    @api.model
    def get_species(self):
        return self.get_variant('especie')

    def get_variant(self, variant_search):
        variant = ''
        if self.is_product_variant:
            variant_res = self.attribute_value_ids.filtered(
                lambda a: a.attribute_id.name in [
                    str.upper(variant_search),
                    str.lower(variant_search),
                    variant_search.capitalize()
                ]
            )
            if variant_res:
                variant = variant_res[0].name
        return variant
