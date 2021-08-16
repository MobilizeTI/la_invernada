from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class StockMove(models.Model):
    _inherit = 'stock.move'
    
    @api.multi
    def _get_price_unit_invoice(self, inv_type, partner, qty=1):
        price_unit = super(StockMove, self)._get_price_unit_invoice(inv_type, partner, qty)
        move = fields.first(self)
        if move.precio_unitario:
            price_unit = move.precio_unitario
        return price_unit
    
    @api.model
    def _get_extra_domain(self):
        user_model = self.env['res.users']
        domain = []
        location_ids = []
        if not user_model.has_group('stock.group_stock_manager') \
                and not user_model.has_group('l10n_cl_stock.group_validate_guias') \
                and not self.env.context.get('show_all_location',False):
            location_ids = user_model.get_all_location().ids
            if location_ids:
                domain.append('|')
                domain.append(('location_id','in', location_ids))
                domain.append(('location_dest_id','in', location_ids))
        return domain
    
    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        args.extend(self._get_extra_domain())
        res = super(StockMove, self)._search(args=args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
        return res
    
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        domain.extend(self._get_extra_domain())
        res = super(StockMove, self).read_group(domain=domain, fields=fields, groupby=groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return res
    
    @api.multi
    def _assign_picking(self):
        return super(StockMove, self.with_context(show_all_location=True))._assign_picking()
    
    @api.multi
    def _action_assign(self):
        return super(StockMove, self.with_context(show_all_location=True))._action_assign()
