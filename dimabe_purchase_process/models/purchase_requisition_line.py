from odoo import fields, models, api
from odoo.addons import decimal_precision as dp


class PurchaseRequisitionLine(models.Model):
    _inherit = 'purchase.requisition.line'

    account_analytic_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        required=True
    )

    price_unit = fields.Float(
        string='Unit Price',
        digits=dp.get_precision('Product Price'),
        required=True,
        default=None
    )
