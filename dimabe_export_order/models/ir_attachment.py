from odoo import models, fields, api


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.model
    def create(self,values_list):
        for item in self:
            models._logger.error("id {}".format(item.id))
            models._logger.error(item.id)
            models._logger.error(item.id)
            models._logger.error(item.id)
            models._logger.error(item.id)
            models._logger.error(item.id)
            models._logger.error(item.id)
            models._logger.error(item.id)
            models._logger.error(item.id)
            models._logger.error(item.id)
        res = super(StockProductionLotSerial, self).create(values_list)
        return res
