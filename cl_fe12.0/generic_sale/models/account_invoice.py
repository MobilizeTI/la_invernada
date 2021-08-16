from odoo import models, api, fields


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def _get_fields_to_split(self):
        fields_list = super(AccountInvoice, self)._get_fields_to_split()
        fields_list.extend([
            'team_id', 'partner_shipping_id'
        ])
        return fields_list
