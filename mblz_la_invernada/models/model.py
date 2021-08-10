# -*- coding: utf-8 -*-

import logging
import datetime

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def remove_account_move_lines(self):
        to_removes = [
            # ['account.voucher.line', ],
            # ['account.voucher', ],
            # ['account.bank.statement', ],
            # ['account.bank.statement.line', ],
            # ['account.payment', ],
            # ['account.analytic.line', ],
            ['account.invoice.line', ],
            # ['account.invoice', ],
            # ['account.partial.reconcile', ],
            # ['account.move.line', ],
            # ['account.move', ],

            ##### stock ######
            # ['stock.quant', ],
            # ['stock.quant.package', ],
            # ['stock.quant.move.rel', ],
            # ['stock.move.line', ],
            # ['stock.move', ],
            # ['stock.pack.operation', ],
            # ['stock.picking', ],
            # ['stock.scrap', ],
            # ['stock.inventory.line', ],
            # ['stock.inventory', ],
            # ['stock.production.lot', ],
            # ['stock.fixed.putaway.strat', ],
            # ['make.procurement', ],
            # ['procurement.order', ],
            # ['procurement.group', ],
        ]
        try:
            for line in to_removes:
                obj_name = line[0]
                obj = self.pool.get(obj_name)
                if obj:
                    sql = "delete from {} where create_date <= '2020-12-31 23:59:59'".format(obj._table)
                    self._cr.execute(sql)
        except Exception as e:
            raise Warning(e)
        return True
