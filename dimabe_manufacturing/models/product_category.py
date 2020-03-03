from odoo import fields, models, api


class ProductCategory(models.Model):
    _inherit = 'product.category'

    reserve_ignore = fields.Boolean('Ignorar al reservar en producción')

    @api.model
    def set_child_reserve_ignore(self):
        if self.child_id:
            for child_id in self.child_id:
                child_id.reserve_ignore = self.reserve_ignore
                if child_id.child_id:
                    child_id.set_child_reserve_ignore()

    @api.model
    def create(self, values_list):

        res = super(ProductCategory, self).create(values_list)

        if res.child_id:
            res.set_child_reserve_ignore()
        return res

    @api.multi
    def write(self, values):

        res = super(ProductCategory, self).write(values)

        for item in self:
            if item.child_id:
                item.set_child_reserve_ignore()

        return res
