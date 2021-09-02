from odoo import models, fields, api
from odoo.exceptions import ValidationError
import json
import requests
import inspect
from datetime import date
import re
from pdf417 import encode, render_image, render_svg
import xml.etree.ElementTree as ET
import base64
from io import BytesIO
from math import floor
from datetime import date

import logging
_logger = logging.getLogger('TEST invoice =======')


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
    def format_amount(self, amount):
        return '$ {:,.0f}'.format(round(amount)).replace(",",".")

    def get_amount_exempt(self):
        lineas_exentas = self.invoice_line_ids.filtered(lambda a: 'Exento' in a.invoice_line_tax_ids.mapped('name'))
        monto_exempt = 0.0
        for l in lineas_exentas:
            monto_exempt += l.price_subtotal
        return monto_exempt

    def get_amount_neto(self):
        return abs(self.amount_untaxed - self.get_amount_exempt())

    def get_today(self):
        return date.today().strftime('%Y-%m-%d')
    
    # @api.multi
    def write(self, vals):
        _logger.info('LOG:  ----> journal {}'.format(self._context.get('journal_id')))
        _logger.info('LOG:  ----> journal {}'.format(vals.get('journal_id')))
        res = super(AccountInvoice, self).create(vals)
        return res

