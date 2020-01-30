from odoo import fields, models, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    stock = fields.Many2one("stock.production.lot.serial")

    product_qty = fields.Float(rel="stock.product_qty")

    stock_id = fields.Char(rel="stock.stock_product_lot_id")


    @api.multi
    def calculate_done(self):
        for item in self:
            models._logger.error('22222222222222222222222222222222{}'.format(stock_id))
            for line_id in item.finished_move_line_ids:
                line_id.qty_done = line_id.lot_id.total_serial

    @api.multi
    def button_mark_done(self):
        self.calculate_done()
        return super(MrpProduction, self).button_mark_done()
