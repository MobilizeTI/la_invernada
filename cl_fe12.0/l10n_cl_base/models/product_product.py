from odoo import models, api, fields, tools
from odoo.exceptions import UserError, ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    @api.model
    def create(self, vals):
        if vals.get('barcode'):
            if self.search_count([('barcode','=', vals['barcode'])]) > 0:
                raise UserError("El codigo ean: %s ya existe y no se puede repetir, por favor verifique" % vals['barcode'])
        new_rec = super(ProductProduct, self).create(vals)
        return new_rec
    
    @api.multi
    def write(self, vals):
        if vals.get('barcode'):
            if self.search_count([('barcode','=', vals['barcode']), ('id','not in', self.ids)]) > 0:
                raise UserError("El codigo ean: %s ya existe y no se puede repetir, por favor verifique" % vals['barcode'])
        res = super(ProductProduct, self).write(vals)
        return res

    def _get_domain_locations(self):
        ctx = self.env.context.copy()
        if not ctx.get('show_all_stock', False):
            location_recs = self.env['res.users'].get_all_location()
            if location_recs:
                ctx['location'] = location_recs.ids
        return super(ProductProduct, self.with_context(ctx))._get_domain_locations()
