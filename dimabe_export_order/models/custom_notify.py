from odoo import models, fields


class CustomNotify(models.Model):
    _name = 'custom.notify'

    partner_id = fields.Many2one('res.partner', string='Cliente', required=True, domain=[('customer', '=', True)])

    position = fields.Integer("Posición",nullable=True)