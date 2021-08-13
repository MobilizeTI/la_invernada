from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import Warning, UserError, ValidationError


class WizardAcceptDocumentXml(models.TransientModel):
    _name = 'wizard.accept.document.xml'
    _description = 'Asistente para aceptar documentos XML' 
    
    product_type = fields.Selection([
        ('product','Almacenable'),
        ('service','Servicio'),
        ], string='Tipo de Producto')
    product_options = fields.Selection([
        ('sale','Vendible'),
        ('no_sale','No Vendible'),
        ], string='El producto es')
    partner_account_id = fields.Many2one('account.account', 'Cuenta Contable(Empresa)', required=False)
    account_id = fields.Many2one('account.account', 'Cuenta Contable(Detalle)')
    account_analytic_id = fields.Many2one('account.analytic.account', 'Cuenta de Gasto')
    force_create_product = fields.Boolean('Crear Producto?')
    no_create_lines = fields.Boolean('No Crear detalle?')
    auto_validate_invoice = fields.Boolean('Validar Automaticamente Factura?')
    product_service_id = fields.Many2one('product.product', 'Producto a usar')
    pricelist_id = fields.Many2one('product.pricelist', 'Tarifa de Venta')

    @api.model
    def default_get(self, fields_list):
        values = super(WizardAcceptDocumentXml, self).default_get(fields_list)
        #obtener los valores por defecto para el asistente donde se suben los xml
        #los campos se llaman iguales
        ir_defaults = self.env['ir.default'].get_model_defaults('sii.dte.upload_xml.wizard')
        for name in fields_list:
            if name in ir_defaults:
                values[name] = ir_defaults[name]
                continue
        return values
    
    @api.onchange('product_type',)
    def _onchange_product_type(self):
        if self.product_type == 'service':
            self.product_options = 'no_sale'
            
    def _prepare_values_aditionals(self):
        values = {}
        values['raise_error'] = True
        values['default_product_type'] = self.product_type
        values['default_auto_validate_invoice'] = self.auto_validate_invoice
        values['default_product_options'] = self.product_options
        values['default_force_create_product'] = self.force_create_product
        if self.pricelist_id:
            values['default_pricelist_id'] = self.pricelist_id.id
        if self.partner_account_id:
            values['default_partner_account_id'] = self.partner_account_id.id
        if self.account_id:
            values['default_account_id'] = self.account_id.id
        if self.account_analytic_id:
            values['default_account_analytic_id'] = self.account_analytic_id.id
        values['default_no_create_lines'] = self.no_create_lines
        if self.product_service_id:
            values['default_product_service_id'] = self.product_service_id.id
        return values
    
    @api.multi
    def action_accept(self):
        ctx = self.env.context.copy()
        ctx.update(self._prepare_values_aditionals())
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        return self.env[active_model].browse(active_ids).with_context(ctx).accept_document()
