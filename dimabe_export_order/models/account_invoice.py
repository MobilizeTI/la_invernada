
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