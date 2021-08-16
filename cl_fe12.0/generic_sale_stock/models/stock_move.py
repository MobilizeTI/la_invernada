from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _

class StockMove(models.Model):
    _inherit = 'stock.move'
    
    @api.multi
    def _action_propagate_valuation(self):
        for move in self:
            # factura desde un pedido de venta
            if move.sale_line_id:
                # las ventas tienen signo negativo, por ello multiplicar x -1
                # las devoluciones al ser entradas tendrian signo positivo y al multiplicar por -1 quedan en negativo
                move.sale_line_id.write({'amount_cost': move.sale_line_id.amount_cost + (move.value * -1)})
                for invoice_line in move.sale_line_id.invoice_lines:
                    invoice_line.write({'amount_cost': invoice_line.amount_cost + (move.value * -1)})
            # factura creada desde picking, o picking creado desde una factura manual
            elif move.invoice_line_ids:
                for invoice_line in move.invoice_line_ids:
                    invoice_line.write({'amount_cost': invoice_line.amount_cost + (move.value * -1)})
        return super(StockMove, self)._action_propagate_valuation()