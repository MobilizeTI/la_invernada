from odoo import models, fields, api, _
from odoo.tools.misc import format_date, DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta


class AccountGeneralLedgerReport(models.AbstractModel):
    _inherit = 'account.general.ledger'

    @api.model
    def _get_columns_name(self, options):
        columns_names = [
            {'name': 'Cuenta'},
            {'name': _('Date'), 'class': 'date'},
            {'name': _('Communication')},
            {'name': _('Cuenta Analítica')},
            {'name': _('Partner')},
            {'name': _('Debit'), 'class': 'number'},
            {'name': _('Credit'), 'class': 'number'},
            {'name': _('Balance'), 'class': 'number'}
        ]
        if self.user_has_groups('base.group_multi_currency'):
            columns_names.insert(4, {'name': _('Currency'), 'class': 'number'})
        return columns_names