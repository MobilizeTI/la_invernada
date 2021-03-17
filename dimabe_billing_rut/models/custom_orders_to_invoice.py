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

    is_multiple_dispatch = fields.Char(string="Es Despacho Multiple?", compute="_compute_is_multiple_dispatch")

    main_dispatch = fields.Char(string="Despacho Princiapl", compute="_compute_main_dispatch")

    invoice_id = fields.Many2one(
        'account.invoice',
        index=True,
        copy=False,
        string="Pedido"
    )


    required_loading_date = fields.Datetime(string="Fecha Requerida de Carga", compute="_compute_required_loading_date")

    def _compute_is_multiple_dispatch(self):
        for item in self:
            if item.stock_picking_id and item.stock_picking_id != 0:
                stock = self.env['stock.picking'].search([('id','=',item.stock_picking_id)])
                if not stock.is_child_dispatch or stock.is_child_dispatch == '' or stock.picking_principal_id:
                    item.is_multiple_dispatch = "Si"
                else:
                    item.is_multiple_dispatch = ""
    
    def _compute_main_dispatch(self):
        for item in self:
            if item.stock_picking_id and item.stock_picking_id != 0:
                stock = self.env['stock.picking'].search([('id','=',item.stock_picking_id)])
                if stock.picking_principal_id or stock.picking_principal_id != '':
                    item.main_dispatch = stock.picking_principal_id.name
                else:
                    item.main_dispatch = ""

    def _compute_container_number(self):
        for item in self:
            if item.stock_picking_id and item.stock_picking_id != 0:
                stock = self.env['stock.picking'].search([('id','=',item.stock_picking_id)])

                if not stock.is_child_dispatch or stock.is_child_dispatch == '' or stock.picking_principal_id:
                    item.container_number = stock.container_number
                else:
                    item.container_number = ''
      
    def _compute_required_loading_date(self):
        for item in self:
            if item.stock_picking_id and item.stock_picking_id != 0:
                stock = self.env['stock.picking'].search([('id','=',item.stock_picking_id)])
                if not stock.is_child_dispatch or stock.is_child_dispatch == '':
                    item.required_loading_date = stock.required_loading_date


  
    
