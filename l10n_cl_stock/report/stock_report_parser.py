from collections import OrderedDict

from odoo import SUPERUSER_ID
from odoo import models, api
from odoo.tools.misc import formatLang
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class StockReport(models.AbstractModel):    
    _name = 'report.stock.report_picking'
    _description = 'Reporte de Picking' 
    
    def _get_lines_by_template(self, picking):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        show_quantities_grouped = ICPSudo.get_param('show_quantities_grouped', default='show_detail')
        data_by_template = OrderedDict()
        colors = []
        line_key = False
        company = picking.company_id or self.env.user.company_id
        atribute_size = [company.size_calzado_id.id, company.size_vestuario_id.id]
        for line in picking.move_lines:
            colors = []
            for atribute in line.product_id.attribute_value_ids.filtered(lambda x: x.attribute_id == company.color_id):
                colors.append(atribute.name)
            colors = ", ".join(colors)
            line_key = (line.product_id.product_tmpl_id, colors, line.discount, line.precio_unitario)
            if show_quantities_grouped == 'show_detail':
                line_key = (line, "", line.discount, line.precio_unitario)
            quantity = line.product_uom_qty
            data_by_template.setdefault(line_key, {})
            data_by_template[line_key].setdefault('price_subtotal', 0.0)
            data_by_template[line_key].setdefault('price_tax_included', 0.0)
            data_by_template[line_key].setdefault('quantity', 0.0)
            data_by_template[line_key].setdefault('ordered_qty', 0.0)
            data_by_template[line_key].setdefault('qty_done', 0.0)
            data_by_template[line_key].setdefault('attributes', [])
            data_by_template[line_key]['quantity'] += quantity
            data_by_template[line_key]['ordered_qty'] += quantity
            data_by_template[line_key]['qty_done'] += line.quantity_done
            data_by_template[line_key]['default_code'] = line.product_id.default_code
            data_by_template[line_key]['name'] = line.name if line.name  else line.product_id.name
            data_by_template[line_key]['product_template'] = line.product_id.product_tmpl_id
            data_by_template[line_key]['uom_id'] = line.product_uom.name
            data_by_template[line_key]['discount'] = line.discount
            data_by_template[line_key]['price_subtotal'] += line.subtotal
            data_by_template[line_key]['price_tax_included'] += line.subtotal #FIXME: stock.move no tiene campo price_tax_included
            data_by_template[line_key]['price_unit'] = line.precio_unitario  
            data_by_template[line_key]['color'] = colors
            for atribute in line.product_id.attribute_value_ids:
                if atribute.attribute_id.id in atribute_size:
                    data_by_template[line_key]['attributes'].append("<b>%s</b>/%s" % (atribute.name, formatLang(picking.env, quantity, dp='Product Unit of Measure')))
        return list(data_by_template.values())

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data:
            data = {}
        picking_model = self.env['stock.picking']
        ICPSudo = self.env['ir.config_parameter'].sudo()
        docargs = {
            'doc_ids': docids,
            'doc_model': picking_model._name,
            'data': data,
            'docs': picking_model.sudo().browse(docids),
            'get_lines': self._get_lines_by_template,
            'show_atributes_on_reports': ICPSudo.get_param('show_atributes_on_reports', default='hide_attributes'),
        }
        return docargs

class StockPickingReport(models.AbstractModel):
    _inherit = 'report.stock.report_picking'
    _name = 'report.stock.report_deliveryslip'
    
class StockPickingGuiaReport(models.AbstractModel):
    _inherit = 'report.stock.report_picking'
    _name = 'report.l10n_cl_stock_picking.dte_stock_picking'


class StockReportCedible(models.AbstractModel):
    _inherit = 'report.stock.report_picking'
    _name = 'report.l10n_cl_stock_picking.stock_picking_cedible'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        docargs = super(StockReportCedible, self)._get_report_values(docids, data)
        docargs['cedible'] = True
        return docargs
