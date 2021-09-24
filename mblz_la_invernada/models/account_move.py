# -*- coding: utf-8 -*-
import logging
import datetime

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = 'account.move'

    def format_amount(self, amount, usd=False):
        if usd:
            mnt = '$ {:,.2f}'.format(amount).split('.')
            int_part = mnt[0].replace(',', '.')
            dec_part = mnt[1]
            return '{},{}'.format(int_part, dec_part)
        return '$ {:,.0f}'.format(round(amount)).replace(",",".")
