from odoo import models, fields, api
from .rut_helper import prepare_rut


class ResPartner(models.Model):
    _inherit = 'res.partner'

    invoice_rut = fields.Char(
        'Rut Facturación'
    )

    giro = fields.Char(
        'Giro'
    )

    @api.model
    def create(self, values_list):
        prepare_rut(values_list)
        return super(ResPartner, self).create(values_list)

    @api.multi
    def write(self, values):
        prepare_rut(values)
        return super(ResPartner, self).write(values)
