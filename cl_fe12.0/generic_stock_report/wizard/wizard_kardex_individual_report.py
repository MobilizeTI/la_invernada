from odoo import models, api, fields


class WizardKardexIndividualReport(models.TransientModel):
    _name = 'wizard.kardex.individual.report'
    _description = 'Asistente para kardex individual'
    
    product_id = fields.Many2one('product.product', 'Producto', required=False, help="",)
    location_id = fields.Many2one('stock.location', 'Ubicación', required=False, help="",)
    date_from = fields.Datetime('Desde', help="",)
    date_to = fields.Datetime('Hasta', help="",)
    
    @api.multi
    def _get_context_for_report(self):
        self.ensure_one()
        ctx = self.env.context.copy()
        ctx.update({'product_id': self.product_id.id,
                    'location_id': self.location_id.id,
                    'date_from': self.date_from or '',
                    'date_to': self.date_to or '',
                    })
        return ctx
    
    @api.multi
    def action_print_report(self):
        company = self.env.user.company_id
        ctx = self._get_context_for_report()
        ctx['active_model'] = 'res.company'
        ctx['active_ids'] = [company.id]
        ctx['active_id'] = company.id
        return self.env.ref('generic_stock_report.kardex_individual_report').with_context(ctx).report_action(company, ctx)
