from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger('TEST ========================')


class DiaryAccountMoveLineReport(models.AbstractModel):
    _name = 'report.mblz_la_invernada.report_diary_account_move_pdf'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("El contenido del reporte esta vacio, El reporte no puede imprimirse."))
        


        report = self.env['ir.actions.report']._get_report_from_name('mblz_la_invernada.report_diary_account_move_pdf')
        lines = self.get_move_lines(data['form']['date'], data['form']['company_get_id'][0])
        if not lines:
            raise UserError(_("No hay Apuntes para este día."))
        report_data = {            
            'doc_ids': lines[0].get('move'),
            'doc_model': report.model,
            'docs': lines[0].get('move'),
            'date': data['form']['date'],
            'company_get_id': data['form']['company_get_id'],
            'get_move_lines': lines,
        }
        _logger.info('LOG:.    test data report {}'.format(report_data))
        return report_data

    def get_move_lines(self, date, company_id):
        domain = [
            ('date', '=', date),
            ('company_id.id', '=', company_id)
            ]
        res = []
        
        lines = self.env['account.move.line'].sudo().search(domain, order='date asc')
        moves = list(set([line.move_id for line in lines]))
        for move in moves:
            move_lines = lines.filtered(lambda l: l.move_id == move)
            res.append({
                'move': move,
                'lines': move_lines
            })
        
        return res

        # report= {
        #     'doc_ids': account.move(15,), 
        #     'doc_model': 'account.move.line', 
        #     'docs': account.move(15,), 'date': '2019-06-19', 
        #     'company_get_id': [3, 'Servicios La Invernada SPA'], 
        #     'get_move_lines': [
        #         {
        #             'move': account.move(15,), 
        #             'lines': account.move.line(43, 44)
        #         }, 
        #         {
        #             'move': account.move(15,), 
        #             'lines': account.move.line(43, 44)
        #         }
        #         ]}
