from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class StockInventory(models.Model):
    _inherit = 'stock.inventory'
    
    @api.model
    def _find_inventory_from_pos(self, inventory_id):
        return super(StockInventory, self.with_context(show_all_location=True))._find_inventory_from_pos(inventory_id)
    
    @api.multi
    def _is_line_valid_from_pos(self, product, vals_line_pos):
        product_ok = super(StockInventory, self)._is_line_valid_from_pos(product, vals_line_pos)
        if self.product_brand_id and self.product_brand_id != product.product_brand_id:
            product_ok = False
        if self.product_sub_categ_id and self.product_sub_categ_id != product.product_sub_categ_id:
            product_ok = False
        if self.product_gender_id and self.product_gender_id != product.product_gender_id:
            product_ok = False
        if self.product_sub_gender_id and self.product_sub_gender_id != product.product_sub_gender_id:
            product_ok = False
        if self.product_ua_id and self.product_ua_id != product.product_ua_id:
            product_ok = False
        if self.product_siluet_app_id and self.product_siluet_app_id != product.product_siluet_app_id:
            product_ok = False
        if self.product_siluet_ftw_id and self.product_siluet_ftw_id != product.product_siluet_ftw_id:
            product_ok = False
        if self.product_siluet_hw_id and self.product_siluet_hw_id != product.product_siluet_hw_id:
            product_ok = False
        if self.product_silo_ftw_id and self.product_silo_ftw_id != product.product_silo_ftw_id:
            product_ok = False
        if self.product_tem_prov_id and self.product_tem_prov_id != product.product_tem_prov_id:
            product_ok = False
        if self.product_ingreso_id and self.product_ingreso_id != product.product_ingreso_id:
            product_ok = False
        if self.product_year_id and self.product_year_id != product.product_year_id:
            product_ok = False
        if self.product_categ_id and self.product_year_id != product.product_year_id:
            product_ok = False
        return product_ok
    
    @api.multi
    def _get_domain_for_products_to_zero(self):
        domain = super(StockInventory, self)._get_domain_for_products_to_zero()
        if self.product_brand_id:
            domain.append(('product_brand_id', '=', self.product_brand_id.id))
        if self.product_sub_categ_id:
            domain.append(('product_sub_categ_id', '=', self.product_sub_categ_id.id))
        if self.product_gender_id:
            domain.append(('product_gender_id', '=', self.product_gender_id.id))
        if self.product_sub_gender_id:
            domain.append(('product_sub_gender_id', '=', self.product_sub_gender_id.id))
        if self.product_ua_id:
            domain.append(('product_ua_id', '=', self.product_ua_id.id))
        if self.product_siluet_app_id:
            domain.append(('product_siluet_app_id', '=', self.product_siluet_app_id.id))
        if self.product_siluet_ftw_id:
            domain.append(('product_siluet_ftw_id', '=', self.product_siluet_ftw_id.id))
        if self.product_siluet_hw_id:
            domain.append(('product_siluet_hw_id', '=', self.product_siluet_hw_id.id))
        if self.product_silo_ftw_id:
            domain.append(('product_silo_ftw_id', '=', self.product_silo_ftw_id.id))
        if self.product_tem_prov_id:
            domain.append(('product_tem_prov_id', '=', self.product_tem_prov_id.id))
        if self.product_ingreso_id:
            domain.append(('product_ingreso_id', '=', self.product_ingreso_id.id))
        if self.product_year_id:
            domain.append(('product_year_id', '=', self.product_year_id.id))
        if self.product_categ_id:
            domain.append(('categ_id', '=', self.product_categ_id.id))
        return  domain
