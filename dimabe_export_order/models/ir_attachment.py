from odoo import models, fields, api
import os


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    counter = fields.Integer("Contador")

    stock_picking_id = fields.Many2one('stock.picking')

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            for field in ('file_size', 'checksum'):
                values.pop(field, False)
            values = self._check_contents(values)
            values = self._make_thumbnail(values)
            self.browse().check('write', values=values)
        return super(IrAttachment, self).create(vals_list)
