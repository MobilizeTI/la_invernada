from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class StockLocation(models.Model):
    _inherit = 'stock.location'
    
    @api.model
    def _get_extra_domain(self):
        user_model = self.env['res.users']
        domain = []
        location_ids = []
        if not user_model.has_group('stock.group_stock_manager') \
                and not user_model.has_group('l10n_cl_stock.group_validate_guias') \
                and self.env.context.get('filter_my_location',False):
            location_ids = user_model.get_all_location().ids
            if location_ids:
                domain.append(('id','in', location_ids))
        return domain
    
    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        args.extend(self._get_extra_domain())
        res = super(StockLocation, self)._search(args=args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
        return res
    
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        domain.extend(self._get_extra_domain())
        res = super(StockLocation, self).read_group(domain=domain, fields=fields, groupby=groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return res
