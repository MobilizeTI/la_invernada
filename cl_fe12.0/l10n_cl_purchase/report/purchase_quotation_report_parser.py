from collections import OrderedDict

from odoo import models, api, fields, tools
from odoo.tools.misc import formatLang
from odoo import SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class PurchaseQuotationReport(models.AbstractModel):
    _name = 'report.purchase.report_purchasequotation'
    _description = 'Reporte de Presupuestos de compra' 
    
    def _get_lines_by_template(self, purchase, group_by_date=True):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        show_quantities_grouped = ICPSudo.get_param('show_quantities_grouped', default='show_detail')
        data_by_template = OrderedDict()
        colors = []
        line_key = False
        company = purchase.company_id or self.env.user.company_id
        atribute_size = [company.size_calzado_id.id, company.size_vestuario_id.id]
        for line in purchase.order_line:
            colors = []
            for atribute in line.product_id.attribute_value_ids.filtered(lambda x: x.attribute_id == company.color_id):
                colors.append(atribute.name)
            colors = ", ".join(colors)
            date_planned = fields.Datetime.context_timestamp(self, line.date_planned)
            date_planned_by_group = date_planned.strftime(DF) if group_by_date else False
            line_key = (line.product_id.product_tmpl_id, colors, line.discount, line.price_unit, line.product_uom, date_planned_by_group)
            if show_quantities_grouped == 'show_detail':
                line_key = (line, "", line.discount, line.price_unit, line.product_uom, date_planned_by_group)
            data_by_template.setdefault(line_key, {})
            data_by_template[line_key].setdefault('price_subtotal', 0.0)
            data_by_template[line_key].setdefault('quantity', 0.0)
            data_by_template[line_key].setdefault('qty_received', 0.0)
            data_by_template[line_key].setdefault('qty_invoiced', 0.0)
            data_by_template[line_key].setdefault('attributes', [])
            data_by_template[line_key]['quantity'] += line.product_qty
            data_by_template[line_key]['qty_received'] += line.qty_received
            data_by_template[line_key]['qty_invoiced'] += line.qty_invoiced
            data_by_template[line_key]['default_code'] = line.product_id.default_code
            data_by_template[line_key]['product_uom'] = line.product_uom.name
            data_by_template[line_key]['name'] = line.product_id.name
            data_by_template[line_key]['product_template'] = line.product_id.product_tmpl_id
            data_by_template[line_key]['product_image_small'] = line.product_image_small
            data_by_template[line_key]['product_image_medium'] = line.product_image_medium
            data_by_template[line_key]['product_image'] = line.product_image
            data_by_template[line_key]['discount'] = line.discount
            data_by_template[line_key]['price_subtotal'] += line.price_subtotal
            data_by_template[line_key]['price_unit'] = line.price_unit  
            data_by_template[line_key]['color'] = colors
            data_by_template[line_key]['date_planned'] = date_planned.strftime(DTF)
            for atribute in line.product_id.attribute_value_ids:
                if atribute.attribute_id.id in atribute_size:
                    data_by_template[line_key]['attributes'].append("<b>%s</b>/%s" % (atribute.name, formatLang(purchase.env, line.product_qty, dp='Product Unit of Measure')))
        return list(data_by_template.values())
    
    
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
            'get_lines': self._get_lines_by_template,
            'show_atributes_on_reports': ICPSudo.get_param('show_atributes_on_reports', default='hide_attributes'),
        }
        return docargs
