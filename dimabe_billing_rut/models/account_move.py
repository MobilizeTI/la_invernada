from odoo import api, fields, models


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'mail.thread']
