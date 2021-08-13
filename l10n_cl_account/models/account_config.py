from odoo import models, api, fields, tools


class AccountConfig(models.TransientModel):
    _inherit = 'res.config.settings'
    
    default_product_type = fields.Selection([
        ('product',u'Almacenable'),
        ('service',u'Servicio'),
        ], string=u'Tipo de Producto', 
        default_model='sii.dte.upload_xml.wizard')
    default_product_options = fields.Selection([
        ('sale',u'Vendible'),
        ('no_sale',u'No Vendible'),
        ], string=u'El producto es',
        default_model='sii.dte.upload_xml.wizard')
    default_no_create_lines = fields.Boolean(u'No Crear detalle?',
        default_model='sii.dte.upload_xml.wizard')
    default_auto_validate_invoice = fields.Boolean('Validar Automaticamente Factura?',
        default_model='sii.dte.upload_xml.wizard')
    default_product_service_id = fields.Many2one('product.product', 
        u'Producto a usar', 
        default_model='sii.dte.upload_xml.wizard')
    default_account_id = fields.Many2one('account.account', 
        u'Cuenta Contable', 
        default_model='sii.dte.upload_xml.wizard')
    default_account_analytic_id = fields.Many2one('account.analytic.account', 
        u'Cuenta de Gasto', 
        default_model='sii.dte.upload_xml.wizard')
    
    @api.onchange('default_product_type',)
    def _onchange_product_type(self):
        if self.default_product_type == 'service':
            self.default_product_options = 'no_sale'
