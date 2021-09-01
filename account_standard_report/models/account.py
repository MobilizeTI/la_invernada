# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountAccount(models.Model):
    _inherit = 'account.account'

    compacted = fields.Boolean('Entradas compactas.', help='Si está marcado, no se mostrarán detalles en el informe estándar, solo cantidades compactadas.', default=False)
    type_third_parties = fields.Selection([('no', 'No'), ('supplier', 'Proveedor'), ('customer', 'Cliente')], string='Terceros', required=True, default='no')
