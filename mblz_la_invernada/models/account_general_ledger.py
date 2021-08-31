# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.tools.misc import format_date, DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import logging
_logger = logging.getLogger('TEST PURCHASE')


class AccountGeneralLedgerReport(models.AbstractModel):
    _inherit = "account.general.ledger"

    @api.model
    def _get_columns_name(self, options):
        res = super(AccountGeneralLedgerReport, self)._get_columns_name(options)
        _logger.info('LOG:  --- options {}'.format(options))
        res[0] = {'name': 'Cuentas'}
        res.insert(3, {'name': _('Analítica')})
        return res
    
    # @api.model
    # def _get_columns_name(self, options):
    #     columns_names = [
    #         {'name': 'Cuentas'},
    #         {'name': _('Date'), 'class': 'date'},
    #         {'name': _('Communication')},
    #         {'name': _('Analítica')},
    #         {'name': _('Partner')},
    #         {'name': _('Debit'), 'class': 'number'},
    #         {'name': _('Credit'), 'class': 'number'},
    #         {'name': _('Balance'), 'class': 'number'}
    #     ]
    #     if self.user_has_groups('base.group_multi_currency'):
    #         columns_names.insert(4, {'name': _('Currency'), 'class': 'number'})
    #     return columns_names
    
    @api.model
    def _get_report_name(self):
        return _("Libro Mayor MBLZ")
    
    @api.model
    def _get_general_ledger_lines(self, options, line_id=None):
        res = super(AccountGeneralLedgerReport, self)._get_general_ledger_lines(options, line_id)
        _logger.info('!!!!!')
        return res
        