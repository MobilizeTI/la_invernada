from odoo import models, fields, api
class Carrier(models.Model):

    _name = 'custom.carrier'

    name = fields.Char(
        'Conductor',
        required=True
    )

    rut = fields.Char(
        'Rut',
        required=True
    )

    cell_number = fields.Char('Número de celular')

    truck_patent = fields.Char('Patente Camión')
    
    cart_patent = fields.Char('Patente Carro')

    @api.model
    def create(self, values_list):
        values_list = self._prepare_data(values_list)
        return super(Carrier, self).create(values_list)

    @api.multi
    def write(self, vals):
        vals = self._prepare_data(vals)
        return super(Carrier, self).write(vals)

    def _prepare_data(self, values_list):
        if 'truck_patent' in values_list:
            values_list['truck_patent'] = str.upper(values_list['truck_patent'])
        if 'cart_patent' in values_list:
           values_list['cart_patent'] = str.upper(values_list['cart_patent'])
        return values_list