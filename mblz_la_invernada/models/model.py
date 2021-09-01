# -*- coding: utf-8 -*-

import logging
import datetime

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = 'account.move'

    def format_amount(self, amount):
        return '$ {:,.0f}'.format(round(amount)).replace(",",".")