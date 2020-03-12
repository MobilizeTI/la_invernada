from odoo import models, fields, api


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    data = fields.Char("Image")
