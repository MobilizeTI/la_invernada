# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.tools.translate import _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
import logging
_logger = logging.getLogger(__name__)


class Libro(models.Model):
    _inherit = "account.move.book"

    def _get_date(self, rec):
        if 'date_order' not in rec:
            return super(Libro, self)._get_date(rec)
        date_order = fields.Datetime.context_timestamp(rec, rec.date_order)
        return {
            'FchEmiDoc': date_order.strftime(DF),
            'FchVencDoc': date_order.strftime(DTF),
        }

    def _get_datos(self, rec):
        if 'line_ids' in rec:
            return super(Libro, self)._get_datos(rec)
        TaxMnt =  rec.amount_tax
        Neto = rec.pricelist_id.currency_id.round(sum(line.price_subtotal for line in rec.lines))
        MntExe = rec.exento()
        TasaIVA = self.env['pos.order.line'].search([('order_id', '=', rec.id), ('tax_ids.amount', '>', 0)], limit=1).tax_ids.amount
        Neto -= MntExe
        return Neto, MntExe, TaxMnt, TasaIVA

    def _get_moves(self):
        recs = super(Libro, self)._get_moves()
        if self.move_ids:
            orders = self.env['pos.order'].search([
                ('account_move', 'in', self.move_ids.ids),
                ('sii_document_number', 'not in', [False, '0']),
                ('document_class_id.sii_code', 'not in', [33]), # los pedidos q son factura se pasan a contabilidad, no considerarlo 2 veces
                ])
            for r in orders:
                recs.append(r)
        return recs
