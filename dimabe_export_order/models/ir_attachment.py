from odoo import models, fields, api


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    counter = fields.Integer('Contador',default=0)
