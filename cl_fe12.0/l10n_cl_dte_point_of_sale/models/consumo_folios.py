# -*- coding: utf-8 -*-
from odoo import fields, models, api, tools
from odoo.tools.translate import _
from odoo.exceptions import UserError


class ConsumoFolios(models.Model):
    _inherit = "account.move.consumo_folios"

    def _get_moves(self):
        recs = super(ConsumoFolios, self)._get_moves()
        if self.move_ids:
            orders = self.env['pos.order'].search([
                ('account_move', 'in', self.move_ids.ids),
                ('sii_document_number', 'not in', [False, '0']),
                ('document_class_id.sii_code', 'in', [39, 41, 61]),
                ])
            for r in orders:
                recs.append(r)
        return recs
