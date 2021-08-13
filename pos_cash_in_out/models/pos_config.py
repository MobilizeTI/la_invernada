from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _

class PosConfig(models.Model):

    _inherit = 'pos.config'
    
    enable_cash_in_out = fields.Boolean("Habilitar Ingresar/Sacar Dinero")
    enable_cash_in_out_receipt = fields.Boolean("Imprimir Comprobante de Ingreso/Egreso de dinero")
    
    @api.onchange('cash_control')
    def _onchange_cash_control(self):
        if not self.cash_control:
            self.enable_cash_in_out = False
            
    @api.onchange('enable_cash_in_out')
    def _onchange_enable_cash_in_out(self):
        if not self.enable_cash_in_out:
            self.enable_cash_in_out_receipt = False