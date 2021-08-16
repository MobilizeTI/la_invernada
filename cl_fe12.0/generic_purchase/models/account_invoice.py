from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
    def _prepare_invoice_line_from_po_line(self, line):
        vals = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(line)
        vals['discount'] = line.discount
        vals['discount_value'] = line.discount_value
        return vals
