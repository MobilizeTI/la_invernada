from odoo import fields, models, api, _


class account_journal(models.Model):
    _inherit = 'account.journal'

    credit_card_provider_id = fields.Many2one('credit.card.provider', 
        'Grupo de Tarjeta de credito')
