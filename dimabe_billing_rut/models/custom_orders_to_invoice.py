from odoo import models, fields, api

class CustomOrdersToInvoice(models.Model):
    _name = 'custom.orders.to.invoice'

    stock_picking_id = fields.Integer(string="Despacho Id", required=True)
    #stock_picking_id = fields.Many2one('stock.picking', string="Despacho Id", required=True)

    stock_picking_name = fields.Char(string="Despacho", required=True)

    order_id = fields.Integer(string="Pedido Id", required=True)

    order_name = fields.Char(string="Pedido", required=True)

    product_id = fields.Integer(string="Producto Id", required=True)

    product_name = fields.Char(string="Producto", required=True)

    quantity_remains_to_invoice = fields.Float(string="Cantidada por Facturar")

    quantity_to_invoice = fields.Char(string="Cantidad a Facturar", required=True)

    container_number = fields.Char(string="N° Contenedor", compute="_compute_container_number")

    total_comission = fields.Float(string="Valor Comisión", compute="_compute_total_comission")

    invoice_id = fields.Many2one(
        'account.invoice',
        index=True,
        copy=False,
        string="Pedido"
    )

    total_value = fields.Float(string="Valor Total", compute="_compute_total_value")

    value_per_kilo = fields.Float(string="Valor por Kilo", compute="_compute_value_per_kilo")

    required_loading_date = fields.Datetime(string="Fecha Requerida de Carga", compute="_compute_required_loading_date")

    def _compute_container_number(self):
        for item in self:
            if item.stock_picking_id and item.stock_picking_id != 0:
                if not item.stock_picking_id.is_multiple_dispatch:
                    item.container_number = self.env['stock.picking'].search([('id','=',item.stock_picking_id)]).container_number
                else:
                    item.container_number = ''
    
    def _compute_value_per_kilo(self):
        for item in self:
            if item.stock_picking_id and item.stock_picking_id != 0:
                if not item.stock_picking_id.is_multiple_dispatch:
                    item.value_per_kilo = self.env['stock.picking'].search([('id','=',item.stock_picking_id)]).value_per_kilogram
                else:
                    item.value_per_kilo = 0
    
    def _compute_total_value(self):
        for item in self:
            if item.stock_picking_id and item.stock_picking_id != 0:
                if not item.stock_picking_id.is_multiple_dispatch:
                    item.total_value = self.env['stock.picking'].search([('id','=',item.stock_picking_id)]).total_value
                else:
                    item.total_value = 0
    
    def _compute_required_loading_date(self):
        for item in self:
            if item.stock_picking_id and item.stock_picking_id != 0:
                if not item.stock_picking_id.is_multiple_dispatch:
                    item.required_loading_date = self.env['stock.picking'].search([('id','=',item.stock_picking_id)]).required_loading_date


    def _compute_total_comission(self):
        for item in self:
            if item.stock_picking_id and item.stock_picking_id != 0:
                if not item.stock_picking_id.is_multiple_dispatch:
                    item.total_comission = self.env['stock.picking'].search([('id','=',item.stock_picking_id)]).total_commission
                else:
                    item.total_comission = 0
    
  
    
