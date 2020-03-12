from odoo import models, fields, api


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    counter = fields.Integer("Contador")


    @api.model
    def upload_attachment(self):
        for item in self:
            models._logger.error('Id : {}'.format(item.id))
