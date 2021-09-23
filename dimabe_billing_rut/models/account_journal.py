# import base64
# from datetime import date
# import string
# import xlsxwriter
from odoo import fields, models, api
# from collections import Counter
import logging
_logger = logging.getLogger('TEST PURCHASE =======')

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    employee_fee = fields.Boolean('Diario de Honorarios')