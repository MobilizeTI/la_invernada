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
        _logger.info('LOG :_--->>> res {}'.format(res))
        
        return res

        # res = [
        #     {'move': account.move(12335,), 'lines': account.move.line(34555, 34556, 34557)}, 
        #     {'move': account.move(14699,), 'lines': account.move.line(43115, 43116, 43117, 43118)}, 
        #     {'move': account.move(12336,), 'lines': account.move.line(34558, 34559, 34560)}, 
        #     {'move': account.move(12341,), 'lines': account.move.line(34573, 34574, 34575)}, 
        #     {'move': account.move(15254,), 'lines': account.move.line(44660, 44659)}, 
        #     {'move': account.move(12334,), 'lines': account.move.line(34552, 34553, 34554)}, 
        #     {'move': account.move(12339,), 'lines': account.move.line(34567, 34568, 34569)}, 
        #     {'move': account.move(14697,), 'lines': account.move.line(43112, 43111)}, 
        #     {'move': account.move(12343,), 'lines': account.move.line(34579, 34580, 34581)}, 
        #     {'move': account.move(13200,), 'lines': account.move.line(37983, 37981, 37982)}, 
        #     {'move': account.move(14700,), 'lines': account.move.line(43119, 43120, 43121, 43122)}, 
        #     {'move': account.move(13149,), 'lines': account.move.line(37690, 37691, 37692, 37693, 37694, 37695, 37696, 37697, 37698)}, 
        #     {'move': account.move(15253,), 'lines': account.move.line(44657, 44658)}, 
        #     {'move': account.move(14701,), 'lines': account.move.line(43124, 43123)}, 
        #     {'move': account.move(12338,), 'lines': account.move.line(34564, 34565, 34566)}, 
        #     {'move': account.move(12333,), 'lines': account.move.line(34549, 34550, 34551)}, 
        #     {'move': account.move(12337,), 'lines': account.move.line(34561, 34562, 34563)}, 
        #     {'move': account.move(14698,), 'lines': account.move.line(43113, 43114)}]

       