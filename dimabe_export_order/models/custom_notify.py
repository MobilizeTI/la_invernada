from odoo import models, fields


class CustomNotify(models.Model):
    _name = 'custom.notify'

    partner_id = fields.Many2one('res.partner', domain=[('customer', '=', True)], string='Cliente', required=True)

    partner_name = fields.Char(string="Cliente", related='partner_id.name')

    position = fields.Integer("Posición",nullable=True)