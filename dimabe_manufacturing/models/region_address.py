from odoo import fields, models, api


class RegionAddress(models.Model):
    _name = 'region.address'
    _description = 'Región Geográfica'
    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'ya existe una región con este nombre')
    ]

    name = fields.Char(
        'Región',
        required=True
    )

    @api.model
    def create(self, values_list):
        if 'name' in values_list:
            values_list['name'] = str.upper(values_list['name'])
        res = super(RegionAddress, self).create(values_list)
        return res

    @api.multi
    def write(self, values):
        if 'name' in values:
            values['name'] = str.upper(values['name'])
        res = super(RegionAddress, self).write(values)
        return res
