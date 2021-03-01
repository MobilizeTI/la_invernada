
from odoo import models, fields, api
import requests
import json


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'


    notify_ids = fields.Many2many(
            'res.partner',
            domain=[('customer', '=', True)]
        )
    
    consignee_id = fields.Many2one(
        'res.partner',
        'Consignatario',
        domain=[('customer', '=', True)]
    )