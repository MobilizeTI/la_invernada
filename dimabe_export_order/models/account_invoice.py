
from odoo import models, fields, api
import requests
import json


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'


notify_ids = fields.Many2many(
        'res.partner',
        domain=[('customer', '=', True)]
    )