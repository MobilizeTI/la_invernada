from odoo import fields, models, api


class Transport(models.Model):
    _name = 'transport'
    _description = 'patente de camión o carro'

    is_truck = fields.Boolean('Patente de Camión')

    name = fields.Char('Patente')

    @api.model
    def create(self, vals_list):
        if 'name' in vals_list:
            vals_list['name'] = str.upper(vals_list['name'])
        return super(Transport, self).create(vals_list)

    @api.multi
    def write(self, vals):
        if 'name' in vals:
            vals['name'] = str.upper(vals['name'])
        return super(Transport, self).write(vals)
