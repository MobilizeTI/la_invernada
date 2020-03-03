from odoo import models,fields,api

class IrAttachment(models.Model):
    _inherit = "ir.attachment"
    _sort = "create_date asc"




    @api.multi
    def get_full_url(self):
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return base_url
