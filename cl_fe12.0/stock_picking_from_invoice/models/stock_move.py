from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_related_invoices(self):
        """ Overridden from stock_account to return the customer invoices
        related to this stock move.
        """
        rslt = super(StockMove, self)._get_related_invoices()
        invoices = self.mapped('invoice_line_ids.invoice_id').filtered(lambda x: x.state not in ('draft', 'cancel'))
        rslt += invoices
        return rslt
