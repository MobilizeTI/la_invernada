from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger('TEST ========================')


class HrAttendanceSummaryReport(models.AbstractModel):
    _name = 'report.dimabe_billing_rut.report_purchase_book_pdf'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("El contenido del reporte esta vacio, El reporte no puede imprimirse."))

        report = self.env['ir.actions.report']._get_report_from_name('dimabe_billing_rut.account_move_report_action_mblz')
        account = self.env['account.move'].browse(self.ids)
        _logger.info(account)
        return {            
            'doc_ids': self.ids,
            'doc_model': report.model,
            'docs': account,
            'from_date': data['form']['from_date'],
            'to_date': data['form']['to_date'],
            'company_get_id': data['form']['company_get_id'],
            'get_invoices': self.get_invoices(data['form']['from_date'], data['form']['to_date'], data['form']['company_get_id'][0]),
            'get_exempts': self.get_exempts(data['form']['from_date'], data['form']['to_date'], data['form']['company_get_id'][0]),
            'get_debits': self.get_debits(data['form']['from_date'], data['form']['to_date'], data['form']['company_get_id'][0]),
            'get_credits': self.get_credits(data['form']['from_date'], data['form']['to_date'], data['form']['company_get_id'][0])
        }

    def get_invoices(self, from_date, to_date, company_id):
        domain_invoices = [('date', '>=', '2021-07-01'),
                     ('type', 'in', ('in_invoice', 'in_refund')),
                     ('date', '<=', '2021-07-31'), 
                     #('dte_type_id.code', '=', 33),
                     ('company_id.id', '=', 3)]
                #cambio en Order
        res = self.env['account.invoice'].sudo().search(domain_invoices, order='date asc, reference asc') #facturas electronicas
        _logger.info('LOG: ....>>>> ***** dominio factuyras {} res {}'.format(domain_invoices, res))
        return res

    def get_exempts(self, from_date, to_date, company_id):
        return self.env['account.invoice'].sudo().search([('date', '>=', from_date),
                                                                     ('type', 'in', ('in_invoice', 'in_refund')),
                                                                     ('date', '<=', to_date),
                                                                    #('dte_type_id.code', '=', 34),
                                                                     ('company_id.id', '=', company_id)],
                                                                     order='date asc, reference asc')  #ORDENA ASCENDENTE
        
    def get_debits(self, from_date, to_date, company_id):
        return self.env['account.invoice'].sudo().search([('date', '>=', from_date),
                                                                   ('date', '<=', to_date),
                                                                   ('type', 'in', ('out_invoice', 'out_refund')),
                                                                   #('dte_type_id.code', '=', 56),
                                                                   ('company_id.id', '=', company_id)],
                                                                   order='date asc, reference asc') #ORDENA DEBITO ASCENDENTE
    
    def get_credits(self, from_date, to_date, company_id):
        return self.env['account.invoice'].sudo().search([('date', '>=', from_date),
                                                                    ('type', 'in', ('in_invoice', 'in_refund')),
                                                                    ('date', '<=', to_date),
                                                                    #('dte_type_id.code', '=', 61),
                                                                    ('company_id.id', '=', company_id)],
                                                                    order='date asc, reference asc') #ORDENA ASCENDENTE
        