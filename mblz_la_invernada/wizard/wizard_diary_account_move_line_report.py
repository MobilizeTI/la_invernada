import base64
from datetime import date
import string
import xlsxwriter
from odoo import fields, models, api
from collections import Counter
import logging
_logger = logging.getLogger('TEST report =======')

class WizardDiaryAccountMoveLine(models.TransientModel):
    _name = 'account.move.line.diary'
    _description = 'Wizard Libro Diario'

    book_file = fields.Binary("Libro Diario")
    company_get_id = fields.Many2one('res.company', 'Compañía')
    # book_report_name = fields.Char("Libro Diario")
    date = fields.Date('Fecha')

    def generate_diary_book_pdf(self):
        # _logger.info('LOG  ..>><<< OKKKKK')
        self.ensure_one()
        [data] = self.read()
        # data['move_ids'] = self.env.context.get('active_ids', [])
        # lines = self.env['account.move.lines'].browse(data['move_ids'])
        _logger.info('LOG  ..>><<< data {}'.format(data))
        datas = {
            'ids': [],
            'model': 'account.move.line',
            'form': data
        }
        # return self.env.ref('dimabe_billing_rut.honorarios_book_pdf_report').report_action(invoices, data=datas)
        # return self.env.ref('mblz_la_invernada.diary_book_pdf_report').report_action(lines, data=datas)
        return self.env.ref('l10n_cl_balance.action_report_financial').report_action(self, data=datas, config=False)