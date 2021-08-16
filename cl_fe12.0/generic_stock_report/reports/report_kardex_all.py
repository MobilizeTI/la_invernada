from odoo import api, models


class ReportKardexAll(models.AbstractModel):    
    _name = 'report.generic_stock_report.report_kardex_all'
    _description = 'Reporte Kardex general' 

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data:
            data = {}
        company_model = self.env['res.company']
        docargs = {
            'doc_ids': docids,
            'doc_model': company_model._name,
            'data': data,
            'docs': company_model.browse(docids),
        }
        docargs.update(self.env['report.stock.utils'].with_context(data).GetKardexAllData())
        return docargs
