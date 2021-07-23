from odoo import models, api, fields, tools
from odoo.tools.misc import formatLang
from odoo import SUPERUSER_ID


class PosInvoiceReport(models.AbstractModel):    
    _inherit = 'report.point_of_sale.report_invoice'

    @api.model
    def _get_report_values(self, docids, data=None):
        docargs = super(PosInvoiceReport, self)._get_report_values(docids, data)
        ICPSudo = self.env['ir.config_parameter'].sudo()
        docargs['get_lines'] = self.env['report.account.report_invoice']._get_lines_by_template
        docargs['show_atributes_on_reports'] = ICPSudo.get_param('show_atributes_on_reports', default='hide_attributes')
        return docargs
