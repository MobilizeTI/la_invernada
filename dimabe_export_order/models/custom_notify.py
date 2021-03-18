from odoo import models, fields


class CustomNotify(models.Model):
    _name = 'custom.notify'

    partner_id = fields.Many2one('res.partner', domain=[('customer', '=', True)], string='Cliente', required=True)

    partner_name = fields.Char(string="Cliente", related='partner_id.name')

    partner_identifier_type = fields.Char(string="Tipo de Notificador", related='partner_id.client_identifier_id.name')

    partner_identifier_value = fields.Char(string="Valor Notificador", related='partner_id.client_identifier_value')

    partner_contact = fields.Char(string="Contacto", related='partner_id.child_ids[0].name')

    partner_contact_phone = fields.Char(string="Contacto", related='partner_id.child_ids[0].phone')
    
    partner_contact_mobile = fields.Char(string="Contacto", related='partner_id.child_ids[0].mobile')

    position = fields.Integer("Posición",nullable=True)