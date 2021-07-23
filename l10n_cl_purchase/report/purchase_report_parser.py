from odoo import models, api, fields, tools
from odoo.tools.misc import formatLang


class PurchaseReport(models.AbstractModel):    
    _name = 'report.purchase.report_purchaseorder'
    _description = 'Reporte de Pedidos de compra' 
    
    @api.model
    def _get_report_values(self, docids, data=None):
        if not data:
            data = {}
        ICPSudo = self.env['ir.config_parameter'].sudo()
        model = 'purchase.order'
        if data and data.get('is_purchase_plan'):
            model = 'purchase.plan'
            docids = data.get('active_ids', [])
        elif self.env.context.get('is_purchase_plan'):
            model = 'purchase.plan'
        docargs = {
            'doc_ids': docids,
            'doc_model': model,
            'docs': self.env[model].browse(docids),
            'data': data,
            'get_lines': self.env['report.purchase.report_purchasequotation']._get_lines_by_template,
            'show_atributes_on_reports': ICPSudo.get_param('show_atributes_on_reports', default='hide_attributes'),
        }
        return docargs
