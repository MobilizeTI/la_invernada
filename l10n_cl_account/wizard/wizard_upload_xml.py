from lxml import etree

from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import Warning, UserError, ValidationError


class WizardUploadXml(models.TransientModel):
    _inherit = 'sii.dte.upload_xml.wizard'
    
    product_type = fields.Selection(
        [('product','Almacenable'),
         ('service','Servicio'),
         ], string='Tipo de Producto', help="",)
    product_options = fields.Selection(
        [('sale','Vendible'),
         ('no_sale','No Vendible'),
         ], string='El producto es', help="",)
    partner_id = fields.Many2one('res.partner', 'Empresa', required=False, help="",)
    partner_account_id = fields.Many2one('account.account', 'Cuenta Contable(Empresa)', required=False)
    account_id = fields.Many2one('account.account', 'Cuenta Contable(detalle)', required=False)
    account_analytic_id = fields.Many2one('account.analytic.account', 'Cuenta de Gasto', required=False, help="",)
    force_create_product = fields.Boolean('Crear Producto?')
    no_create_lines = fields.Boolean('No Crear detalle?', readonly=False, help="",)
    auto_validate_invoice = fields.Boolean('Validar Automaticamente Factura?')
    product_service_id = fields.Many2one('product.product', 'Producto a usar', required=False, help="",)
    pricelist_id = fields.Many2one('product.pricelist', 'Tarifa de Venta')
    
    @api.onchange('type',)
    def _onchange_invoice_type(self):
        res = {}
        self.partner_account_id = False
        if self.type == 'ventas':
            res['domain'] = {'partner_account_id': [('internal_type', '=', 'receivable'), ('deprecated', '=', False)]}
        else:
            res['domain'] = {'partner_account_id': [('internal_type', '=', 'payable'), ('deprecated', '=', False)]}
        return res
    
    @api.onchange('product_type',)
    def _onchange_product_type(self):
        if self.product_type == 'service':
            self.product_options = 'no_sale'
            
    @api.onchange('product_service_id','type', 'no_create_lines')
    def _onchange_product_service(self):
        if self.no_create_lines and self.product_service_id:
            invoice_type = 'out_invoice' if self.type == 'ventas' else 'in_invoice'
            account = self.env['account.invoice.line'].get_invoice_line_account(invoice_type, self.product_service_id, False, self.env.user.company_id)
            if account:
                self.account_id = account.id
    
    @api.multi
    def confirm(self, ret=False):
        #exigir campos solo cuando no este subiendo xml
        #sino cuando este creando la factura o el pedido de compra
        if not self.pre_process:
            if not self.product_type:
                raise Warning(_("Debe seleccionar el tipo de producto"))
            if not self.product_options:
                raise Warning(_("Debe seleccionar si el producto es vendible o no"))
        return super(WizardUploadXml, self.with_context(auto_validate_invoice=self.auto_validate_invoice)).confirm(ret)
    
    def _prepare_partner_vals(self, data):
        vals = super(WizardUploadXml, self)._prepare_partner_vals(data)
        if self.partner_account_id:
            if self.type == 'ventas':
                vals['property_account_receivable_id'] = self.partner_account_id.id
            else:
                vals['property_account_payable_id'] = self.partner_account_id.id
        return vals
    
    @api.multi
    def _prepare_invoice(self, dte, company_id, journal_document_class_id):
        invoice_vals = super(WizardUploadXml, self)._prepare_invoice(dte, company_id, journal_document_class_id)
        if invoice_vals.get('partner_id'):
            self.partner_id = invoice_vals['partner_id']
        return invoice_vals
    
    def _prepare_line(self, line, document_id, account_id, type, company_id, fpos_id,
                      price_included, tipo_dte):
        invoice_line_vals = super(WizardUploadXml, self)._prepare_line(line, document_id, account_id, type, company_id, fpos_id,
                      price_included, tipo_dte)
        if self.account_id and isinstance(invoice_line_vals[2], dict):
            invoice_line_vals[2]['account_id'] = self.account_id.id
        if self.account_analytic_id and isinstance(invoice_line_vals[2], dict):
            invoice_line_vals[2]['account_analytic_id'] = self.account_analytic_id.id
        return invoice_line_vals
    
    def _get_invoice_lines(self, documento, document_id, account_id, invoice_type, fpos,
                           price_included, company_id, tipo_dte):
        lines = []
        #cuando esta activo que no cree detalles, solo crear una linea con un producto generico
        #esta linea tendra el total de la factura
        if self.no_create_lines and not self.pre_process:
            if not self.product_service_id:
                raise UserError("Debe seleccionar el producto a usar")
            price_unit = float(documento.find("Encabezado/Totales/MntNeto").text)
            tax_use = self.product_service_id.supplier_taxes_id
            #como el precio esta incluido el impuesto
            #espero que el impuesto seleccionado sea configurado con impuestos incluidos
            #asi que calcular el impuesto y tomar el precio sin incluir impuesto
            if price_included and tax_use:
                res = tax_use.compute_all(price_unit)
                price_unit = res['total_excluded']
            lines.append((0,0,{
                'name': self.product_service_id.display_name,
                'product_id': self.product_service_id.id,
                'price_unit': price_unit,
                'quantity': 1,
                'uom_id': self.product_service_id.uom_id.id,
                'account_id': self.account_id.id,
                'invoice_line_tax_ids': [(6, 0, tax_use.ids)],
            }))
            return lines
        lines = []
        for line in documento.findall("Detalle"):
            if float(line.find("MontoItem").text) > 0:
                new_line = self._prepare_line(line, document_id, account_id, invoice_type, company_id, fpos, price_included, tipo_dte)
                if new_line:
                    lines.append(new_line)
        return lines

    @api.multi
    def _find_create_categ(self, data):
        categ_model = self.env['product.category']
        categ_name = self.partner_id.name
        categ_find = categ_model.search([('name','=', categ_name)], limit=1)
        if not categ_find:
            categ_find = categ_model.create({'name': categ_name})
        return categ_find
    
    def get_product_values(self, line, company_id, price_included, tipo_dte):
        values = super(WizardUploadXml, self).get_product_values(line, company_id, price_included, tipo_dte)
        values.update({
            'type': self.product_type,
            'sale_ok': self.product_options == 'sale',
            'available_in_pos': (self.product_options == 'sale' and self.product_type == 'product'),
            'categ_id': self._find_create_categ(line).id,
            'standard_price': values.get('list_price') or 0,
        })
        return values
    
    def _create_prod(self, data, company_id, price_included, tipo_dte):
        product = super(WizardUploadXml, self)._create_prod(data, company_id, price_included, tipo_dte)
        if self.pricelist_id:
            product.list_price = product.with_context(pricelist=self.pricelist_id.id).price
        return product
    
    def _buscar_producto(self, document_id, line, company_id, price_included, tipo_dte):
        default_code = False
        CdgItem = line.find("CdgItem")
        NmbItem = line.find("NmbItem").text
        if NmbItem.isspace():
            NmbItem = 'Producto Genérico'
        if document_id:
            code = ' ' + etree.tostring(CdgItem).decode() if CdgItem is not None else ''
            line_id = self.env['mail.message.dte.document.line'].search(
                [
                    ('sequence', '=', line.find('NroLinDet').text),
                    ('document_id', '=', document_id.id),
                ], limit=1
            )
            if line_id:
                if line_id.product_id:
                    return line_id.product_id.id
            else:
                return False
        query = False
        product_id = False
        if CdgItem is not None:
            for c in line.findall("CdgItem"):
                VlrCodigo = c.find("VlrCodigo")
                if VlrCodigo is None or VlrCodigo.text is None or\
                        VlrCodigo.text.isspace():
                    continue
                TpoCodigo = c.find("TpoCodigo").text
                if TpoCodigo == 'ean13':
                    query = [('barcode', '=', VlrCodigo.text)]
                elif TpoCodigo == 'INT1':
                    query = [('default_code', '=', VlrCodigo.text)]
                default_code = VlrCodigo.text
        if not query:
            query = [('name', '=', NmbItem)]
        product_id = self.env['product.product'].search(query)
        query2 = [('name', '=', document_id.partner_id.id)]
        if default_code:
            query2.append(('product_code', '=', default_code))
        else:
            query2.append(('product_name', '=', NmbItem))
        product_supplier = False
        if not product_id and self.type == 'compras':
            product_supplier = self.env['product.supplierinfo'].search(query2, limit=1)
            if product_supplier and not product_supplier.product_tmpl_id.active:
                raise UserError(_('Plantilla Producto para el proveedor marcado como archivado'))
            product_id = product_supplier.product_id or product_supplier.product_tmpl_id.product_variant_id
            if not product_id:
                #si el producto no existe y es un documento de productos almacenables y que pueden ser vendidos
                #no debo crear productos, estos deben estar previamente creados
                if not self.pre_process and not self.force_create_product and self.product_type == 'product' and self.product_options == 'sale':
                    raise Warning(_("No se encuentra un producto con el nombre: %s codigo: %s, " \
                                    "por favor asegurese que exista uno en el sistema") % (NmbItem, default_code))
                if not product_supplier and not self.pre_process:
                    product_id = self._create_prod(line, company_id, price_included, tipo_dte)
                else:
                    code = ''
                    coma = ''
                    for c in line.findall("CdgItem"):
                        code += coma + c.find("TpoCodigo").text + ' ' + c.find("VlrCodigo").text
                        coma = ', '
                    return NmbItem + '' + code
        elif self.type == 'ventas' and not product_id:
            product_id = self._create_prod(line, company_id, price_included, tipo_dte)
        if not product_supplier and document_id.partner_id and self.type == 'compras':
            product_qty = 1
            if line.find('QtyItem') is not None:
                product_qty = float(line.find('QtyItem').text)
            price = 0
            #si no hay precio unitario, tomar el precio total y dividirlo para la cantidad
            #y eso tomar como precio unitario
            if line.find('PrcItem') is not None:
                price = float(line.find('PrcItem').text)
            else:
                price = float(line.find('MontoItem').text) / product_qty
            if price_included:
                price = product_id.supplier_taxes_id.compute_all(price, self.env.user.company_id.currency_id, 1)['total_excluded']
            supplier_info = {
                'name': document_id.partner_id.id,
                'product_name': NmbItem,
                'product_code': default_code,
                'product_tmpl_id': product_id.product_tmpl_id.id,
                'price': price,
            }
            self.env['product.supplierinfo'].create(supplier_info)
        if not product_id.active:
                raise UserError(_('Producto para el proveedor marcado como archivado'))
        return product_id.id
    
