from odoo import models, fields, api


class ProductCategory(models.Model):
    _inherit = 'product.category'

    warehouse_ids = fields.Many2many(
        'stock.warehouse',
        string='Bodegas en las que se Puede Almacenar'
    )

    is_mp = fields.Boolean(
        'Es MP',
        compute='_compute_is_mp'
    )

    is_canning = fields.Boolean(
        'Es Envase',
        compute='_compute_is_canning'
    )

    is_pt = fields.Boolean(
        'Es PT',
        compute='_compute_is_pt'
    )

    with_suffix = fields.Boolean(
        'Lote con Sufijo'
    )

    @api.one
    def _compute_is_mp(self):
        self.is_mp = 'Materia Prima' in self.name
        if not self.is_mp and self.parent_id:
            self.is_mp = 'Materia Prima' in self.parent_id.name

    @api.one
    def _compute_is_pt(self):
        self.is_pt = 'producto terminado' in str.lower(self.name)
        if not self.is_pt and self.parent_id:
            self.is_pt = 'producto terminado' in str.lower(self.parent_id.name)

    @api.one
    def _compute_is_canning(self):
        self.is_canning = 'Envases' in self.name
        if not self.is_canning and self.parent_id:
            self.is_canning = 'Envases' in self.parent_id.name
