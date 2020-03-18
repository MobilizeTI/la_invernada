from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    region_address_id = fields.Many2one(
        'region.address',
        'Región'
    )