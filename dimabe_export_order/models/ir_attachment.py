from odoo import models,fields,api

class IrAttachment(models.Model):
    _inherit = "ir.attachment"
    _sort = "create_date asc"

    counter = fields.Integer("Contador")

