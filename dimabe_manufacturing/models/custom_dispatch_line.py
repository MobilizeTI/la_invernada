from odoo import fields,models,api

class CustomDispatchLine(models.Model):
    _name = 'custom.dispatch.line'

    sale_id = fields.Many2one('sale.order','Pedido')

    dispatch_id = fields.Many2one('stock.picking','Despacho')

    product_uom_qty = fields.Float('Cantidad')


