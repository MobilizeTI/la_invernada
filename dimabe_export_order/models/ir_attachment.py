from odoo import models, fields, api


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    counter = fields.Integer("Contador")


    @api.model
    def create(self,values_list):
        for item in self:
            models._logger.error('Id : {}'.format(item.id))
        res = super(IrAttachment, self).create(values_list)
        return res
