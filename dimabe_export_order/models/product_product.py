from odoo import models, api, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    packing_type = fields.Char('Tipo de Envase',compute='_compute_packing_type')

    @api.multi
    def _compute_packing_type(self):
        for item in self:
            caning = item.get_variant('tipo de envase')
            models._logger.error(canning)
            item.packing_type = caning