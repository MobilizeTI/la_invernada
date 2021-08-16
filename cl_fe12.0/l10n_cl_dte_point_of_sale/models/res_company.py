from odoo import models, api, fields, tools

class ResCompany(models.Model):

    _inherit = 'res.company'
    
    website_portal_boletas = fields.Char('Website Boletas')
