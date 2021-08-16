from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import models, api, fields
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class WizardKardexIndividualReport(models.TransientModel):
    _name = 'wizard.kardex.all.report'
    _description = 'Asistente para kardex General'
    
    @api.model
    def get_default_start_date(self):
        util_model = self.env['odoo.utils']
        return util_model._change_time_zone((datetime.now() + relativedelta(day=1, minute=0, second=0, hour=0))).strftime(DTF)
    
    @api.model
    def get_default_end_date(self):
        util_model = self.env['odoo.utils']
        return util_model._change_time_zone((datetime.now() + relativedelta(months=+1, day=1, days=-1, hour=23, minute=59, second=59))).strftime(DTF)
    
    start_date = fields.Datetime('Start Date', 
        default=get_default_start_date, help="",)
    end_date = fields.Datetime('End Date', 
        default=get_default_end_date, help="",)
    filter = fields.Selection([
        ('by_product','By Product'),
        ('by_category','By Category'),
        ('by_lot','By Lot'),
        ], string='Filter', default = 'by_category',  help="",)
    location_ids = fields.Many2many('stock.location', 'wizard_kardex_all_location_rel', 'wizard_id', 'location_id', 
        'Locations', help="",)
    category_ids = fields.Many2many('product.category', 'wizard_kardex_all_category_rel', 'wizard_id', 'category_id', 
        'Categories', help="",)
    product_ids = fields.Many2many('product.product', 'wizard_kardex_all_product_rel', 'wizard_id', 'product_id', 
        'Products', help="",)
    lot_ids = fields.Many2many('stock.production.lot', 'wizard_kardex_all_lot_rel', 'wizard_id', 'lot_id', 
        'Lots', help="",)

    @api.multi
    def _get_context_for_report(self):
        self.ensure_one()
        ctx = self.env.context.copy()
        ctx.update({'product_ids': self.product_ids.ids,
                    'category_ids': self.category_ids.ids,
                    'lot_ids': self.lot_ids.ids,
                    'location_ids': self.location_ids.ids,
                    'start_date': self.start_date,
                    'end_date': self.end_date,
                    'filter_type': self.filter,
                    })
        return ctx
    
    @api.multi
    def action_print_report(self):
        company = self.env.user.company_id
        ctx = self._get_context_for_report()
        ctx['active_model'] = 'res.company'
        ctx['active_ids'] = [company.id]
        ctx['active_id'] = company.id
        return self.env.ref('generic_stock_report.kardex_all_report').with_context(ctx).report_action(company, ctx)
