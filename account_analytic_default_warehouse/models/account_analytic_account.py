from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'
    
    @api.model
    def _get_extra_domain(self):
        user_model = self.env['res.users']
        domain = []
        warehouse_ids = []
        analytic_ids = []
        if self.env.context.get('filter_my_warehouse',False):
            warehouse_ids = user_model.get_all_warehouse().ids
        if self.env.context.get('warehouse_id',False):
            warehouse_ids = [self.env.context['warehouse_id']]
        if warehouse_ids:
            company = self.env.user.company_id
            analytic_model = self.env['account.analytic.default']
            for warehouse_id in warehouse_ids:
                rec = analytic_model.with_context(warehouse_id=warehouse_id).account_get(user_id=self.env.uid, date=fields.Date.context_today(self), company_id=company.id)
                if rec.analytic_id:
                    analytic_ids.append(rec.analytic_id.id)
        if analytic_ids:            
            domain.append(('id','in', analytic_ids))
        return domain
    
    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        args.extend(self._get_extra_domain())
        res = super(AccountAnalyticAccount, self)._search(args=args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
        return res
    
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        domain.extend(self._get_extra_domain())
        res = super(AccountAnalyticAccount, self).read_group(domain=domain, fields=fields, groupby=groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return res
