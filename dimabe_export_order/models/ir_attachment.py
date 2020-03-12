from odoo import models, fields, api


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.model
    def create(self):
        res = super(StockProductionLotSerial, self).create(values_list)
        return res
