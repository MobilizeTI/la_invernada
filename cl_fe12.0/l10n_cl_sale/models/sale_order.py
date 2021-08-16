from collections import OrderedDict

from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang


class SaleOrder(models.Model):
	_inherit = 'sale.order'
	
	@api.model
	def _default_warehouse_id(self):
		company = self.env.user.company_id.id
		warehouse_recs = self.env['res.users'].get_all_warehouse()
		if warehouse_recs:
			warehouse_recs = warehouse_recs[0]
		else:
			warehouse_recs = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
		return warehouse_recs 
	
	#reemplazar campo para cambiar la funcion por defecto
	warehouse_id = fields.Many2one('stock.warehouse', 
		default=_default_warehouse_id)
	
	@api.multi
	def _prepare_invoice(self):
		invoice_vals = super(SaleOrder, self)._prepare_invoice()
		invoice_vals['warehouse_id'] = self.warehouse_id.id
		if self.team_id and self.partner_id.document_type_id:
			#si el cliente esta configurado con RUT tomar el tipo de documento para factura
			#caso contario tomar el de boleta
			if self.partner_id.document_type_id.sii_code == 81 or self.env.context.get('force_invoice'):
				if self.warehouse_id.journal_document_class_id:
					invoice_vals['journal_document_class_id'] = self.warehouse_id.journal_document_class_id.id
					invoice_vals['document_class_id'] = self.warehouse_id.journal_document_class_id.sii_document_class_id.id
				elif self.team_id.journal_document_class_id:
					invoice_vals['journal_document_class_id'] = self.team_id.journal_document_class_id.id
					invoice_vals['document_class_id'] = self.team_id.journal_document_class_id.sii_document_class_id.id
			elif self.warehouse_id.journal_document_class_boleta_id:
				invoice_vals['journal_document_class_id'] = self.warehouse_id.journal_document_class_boleta_id.id
				invoice_vals['document_class_id'] = self.warehouse_id.journal_document_class_boleta_id.sii_document_class_id.id
			elif self.team_id.journal_document_class_boleta_id:
				invoice_vals['journal_document_class_id'] = self.team_id.journal_document_class_boleta_id.id
				invoice_vals['document_class_id'] = self.team_id.journal_document_class_boleta_id.sii_document_class_id.id
		return invoice_vals
	
	@api.multi
	def action_invoice_create(self, grouped=False, final=False):
		return super(SaleOrder, self.with_context(warehouse_id=self.warehouse_id.id)).action_invoice_create(grouped, final)
	
	@api.multi
	def action_print_invoice(self):
		invoices = self.mapped('invoice_ids')
		if invoices:
			return invoices.invoice_print()

	@api.multi
	def _get_lines_by_template(self):
		ICPSudo = self.env['ir.config_parameter'].sudo()
		show_quantities_grouped = ICPSudo.get_param('show_quantities_grouped', default='show_detail')
		show_discount_on_report = ICPSudo.get_param('show_discount_on_report', default='percentaje')
		data_by_template = OrderedDict()
		colors = []
		line_key = False
		company = self.company_id or self.env.user.company_id
		atribute_size = [company.size_calzado_id.id, company.size_vestuario_id.id]
		for line in self.order_line:
			colors = []
			for atribute in line.product_id.attribute_value_ids.filtered(lambda x: x.attribute_id == company.color_id):
				colors.append(atribute.name)
			colors = ", ".join(colors)
			line_section_note = ""
			if line.display_type:
				line_section_note = "%s_%s" % (line.display_type, line.name)
			line_key = (line.product_id.product_tmpl_id, colors, line.discount, line.price_unit, line.product_uom, line_section_note, line.tax_id)
			if show_quantities_grouped == 'show_detail':
				line_key = (line, "", line.discount, line.price_unit, line.product_uom, line_section_note, line.tax_id)
			data_by_template.setdefault(line_key, {})
			data_by_template[line_key].setdefault('price_subtotal', 0.0)
			data_by_template[line_key].setdefault('price_total', 0.0)
			data_by_template[line_key].setdefault('quantity', 0.0)
			data_by_template[line_key].setdefault('attributes', [])
			data_by_template[line_key]['quantity'] += line.product_uom_qty
			data_by_template[line_key]['default_code'] = line.product_id.default_code
			data_by_template[line_key]['product_uom'] = line.product_uom.name
			data_by_template[line_key]['name'] = line.product_id.name
			data_by_template[line_key]['descripcion'] = line.product_id.description_sale
			data_by_template[line_key]['line_name'] = line.name
			data_by_template[line_key]['display_type'] = line.display_type
			data_by_template[line_key]['tax_id'] = line.tax_id
			data_by_template[line_key]['product_image_small'] = line.product_image_small
			data_by_template[line_key]['product_image_medium'] = line.product_image_medium
			data_by_template[line_key]['product_image'] = line.product_image
			data_by_template[line_key]['discount'] = line.discount if show_discount_on_report == 'percentaje' else line.discount_value
			data_by_template[line_key]['price_subtotal'] += line.price_subtotal
			data_by_template[line_key]['price_total'] += line.price_total
			data_by_template[line_key]['price_unit'] = line.price_unit  
			data_by_template[line_key]['color'] = colors
			for atribute in line.product_id.attribute_value_ids:
				if atribute.attribute_id.id in atribute_size:
					data_by_template[line_key]['attributes'].append("<b>%s</b>/%s" % (atribute.name, formatLang(self.env, line.product_uom_qty, dp='Product Unit of Measure')))
		return list(data_by_template.values())

class SaleOrderLine(models.Model):

	_inherit = 'sale.order.line'

	@api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty', 'tax_id')
	def _onchange_discount(self):
		res = super(SaleOrderLine, self)._onchange_discount()
		#redondear el descuento sin decimales
		self.discount = round(self.discount, 0)
		return res

