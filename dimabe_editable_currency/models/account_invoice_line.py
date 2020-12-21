from odoo import models, fields, api

class AccountInvoiceLine(models.Model):

    _inherit = 'account.invoice.line'

    exempt = fields.Selection([
            ('1', 'No afecto o exento de IVA'),
            ('2', 'Producto o servicio no es facturable'),
            ('3', 'Garantía de depósito por envases, autorizados por Resolución especial'),
            ('4', 'Item No Venta'),
            ('5', 'Item a rebajar'),
            ('6', 'Producto/servicio no facturable negativo'),
            ('7', '')
            ], 'Tipo Exento', default='7')

    # VALIDAR QUE INGRESE ALGO EN EXEPT CUANDO ESTE VACIO O EXENTO EN IMPUESTOS
    @api.onchange('invoice_line_ids')
    def valid_exempt(self):
        if len(self.invoice_line_tax_ids) == 0:
            exempt = 1