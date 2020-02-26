from odoo import fields, models, api


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    balance = fields.Float(
        'Saldo',
        compute='_compute_balance',
        store=True
    )

    @api.multi
    @api.depends('quantity', 'reserved_quantity')
    def _compute_balance(self):
        for item in self:
            item.balance = item.quantity - item.reserved_quantity

    @api.model
    def create(self, vals_list):
        res = super(StockQuant, self).create(vals_list)
        res.set_balance_on_lot()
        return res

    @api.multi
    def write(self, vals):
        res = super(StockQuant, self).write(vals)
        for item in self:
            item.set_balance_on_lot()
        return res

    @api.model
    def set_balance_on_lot(self):
        if self.lot_id and self.location_id.name == 'Stock':
            self.lot_id.balance = self.balance


