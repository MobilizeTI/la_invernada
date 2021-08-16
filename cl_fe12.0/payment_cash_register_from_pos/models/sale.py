from odoo import fields, models, api, _

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    @api.model
    def _prepare_invoice_payment(self, invoice, pos_payment_vals):
        payment_vals = super(SaleOrder, self)._prepare_invoice_payment(invoice, pos_payment_vals)
        if pos_payment_vals.get('statement_id'):
            payment_vals['cash_register_id'] = pos_payment_vals.get('statement_id')
            payment_vals['apply_cash_register'] = True
        return payment_vals
