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
        res = super(RegionAddress, self).create(values_list)
        res.name = str.upper(res.name)
        return res

    @api.multi
    def write(self, values):
        res = super(RegionAddress, self).write(values)
        for item in self:
            item.name = str.upper(item.name)
        return res
