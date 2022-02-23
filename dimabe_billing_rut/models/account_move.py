from odoo import api, fields, models


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'mail.thread']
    
    def format_amount(self, amount):
        if self.currency_id.name == 'USD':
            mnt = '$ {:,.2f}'.format(amount).split('.')
            int_part = mnt[0].replace(',', '.')
            dec_part = mnt[1]
            return '{},{}'.format(int_part, dec_part)
        return '$ {:,.2f}'.format(round(amount)).replace(",",".")
