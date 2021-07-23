from odoo import models, api, fields, tools
from odoo.tools.misc import formatLang
from odoo import SUPERUSER_ID


class SaleReport(models.AbstractModel):    
    _name = 'report.sale.report_saleorder'
    _description = 'Reporte de Pedidos de Venta' 

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data:
            data = {}
        sale_model = self.env['sale.order']
        ICPSudo = self.env['ir.config_parameter'].sudo()
        docargs = {
            'doc_ids': docids,
            'doc_model': sale_model._name,
            'data': data,
            'docs': sale_model.browse(docids),
            'show_atributes_on_reports': ICPSudo.get_param('show_atributes_on_reports', default='hide_attributes'),
            'show_discount_on_report': ICPSudo.get_param('show_discount_on_report', default='percentaje'),
        }
        return docargs
