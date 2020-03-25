from odoo import fields, models, api
from ..helpers.dimabe_team import dimabe_team


class ResUser(models.Model):
    _inherit = 'res.users'

    is_dimabe_team = fields.Boolean(
        'Es Equipo Dimabe',
        compute='_compute_is_dimabe_team',
        store=True
    )

    @api.multi
    @api.depends('login')
    def _compute_is_dimabe_team(self):
        for item in self:
            item.is_dimabe_team = item.login in dimabe_team
