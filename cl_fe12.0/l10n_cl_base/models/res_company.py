from odoo import models, api, fields, tools


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    @api.onchange('city_id')
    def _asign_city(self):
        res = super(ResCompany, self)._asign_city()
        if self.city_id:
            self.country_id = self.city_id.state_id.country_id.id
            self.state_id = self.city_id.state_id.id
        else:
            self.country_id = False
            self.state_id = False
            self.city = ""
        return res
