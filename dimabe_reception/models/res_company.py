from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    sag_code = fields.Char('CSG')