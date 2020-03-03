from odoo import models, fields, api
import json
import requests

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    folio_dte = fields