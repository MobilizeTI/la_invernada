
from odoo import models, fields, api
import requests
import json


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    #To Intructuives

    temperature = fields.Char('Temperatura')

    ventilation = fields.Char('Ventilación')

    humidity = fields.Char('Humedad')

    withdrawal_deposit = fields.Many2one('custom.withdrawal.deposits',string="Depósito Retiro")

    freight_payment_term = fields.Many2one('custom.freight.payment.term',string="Termino de Pago Flete")

    safe_type = fields.Many2one('custom.safe.type',string="Tipo de Seguro")

    stacking = fields.Char(string="Stacking")

    cut_off = fields.Char(string="Cut Off")

    dus_second_send = fields.Char(string="D.U.S 2DO.ENVÍO")

    bill_of_lading = fields.Char(string="Conocimiento de Embarque")

    phytosanitary_certificate = fields.Char(string="Certificado Fitosanitario")

    origin_certificate = fields.Char(string="Certificado Origen")

    plant = fields.Many2one('res.partner', string="Planta")

    quality_type = fields.Many2one('custom.quality.type',string="Calidad")

    consolidation = fields.Char(string="Consolidación")

    total_container = fields.Integer(string="Total de Contenedores")

    notify_ids = fields.Many2many(
            'res.partner',
            domain=[('customer', '=', True)]
        )
    
    consignee_id = fields.Many2one(
        'res.partner',
        'Consignatario',
        domain=[('customer', '=', True)]
    )

    order_names = fields.Char(string="Pedidos", compute="_compute_order_ids")

    
    def _compute_order_ids(self):
        for item in self:
            orders = []
            for line in item.invoice_line_ids:
                if line.order_name and line.order_name not in orders:
                    orders.append(line.order_name)
            str_orders = ''
            for o in orders:
                str_orders += o + ' '
            item.order_names = str_orders


    #canning_quantity_ids = fields.Char(string="Cantidad de Sacos",compute="_compute_canning_quantity")


    #def _compute_canning_quantity(self):
    #    canning_quantities = []
    #    custom_invoice_line_ids = self.env['custom.account.invoice.line'].mapped('product_id').search([('invoice_id','=',self.id)])
    #    for line in custom_invoice_line_ids:
    #        for atr in line.product_id.attribute_value_ids:
    #            is_kg = atr.attribute_id.name.find('K')
    #            if atr.attribute_id.name == 'Tipo de envase' and is_kg != 1:
    #                value = atr.name.isdigit()
    #                canning_quantities.append({
    #                    'quantity': line.quantity / value,
    #                    'canning': atr.name
    #                })

    #   return canning_quantities

