from odoo import models, api, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    packing_type = fields.Char('Tipo de Envase',compute='_compute_packing_type')

    @api.multi
    def _compute_packing_type(self):
        for item in self:
            for attr in item.attribute_value_ids:
                models._logger.error(attr.attribute_id.name)
                models._logger.error(attr.name)
                packing_type = attr.name