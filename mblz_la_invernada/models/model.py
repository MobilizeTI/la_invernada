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
            # ['account.invoice', ],
            # ['account.partial.reconcile', ]
            ['account.move', ]
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
