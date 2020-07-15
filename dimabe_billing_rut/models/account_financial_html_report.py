from odoo import models, fields, api


class AccountFinancialHtmlReport(models.Models):
    _inherit = 'account.financial.html.report'

    @api.multi
    def test(self):
        raise models.UserError("Hola")
