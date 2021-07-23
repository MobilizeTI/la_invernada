from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class StockInventory(models.Model):
    _inherit = 'stock.inventory'
    
    @api.model
    def _default_location_id(self):
        user_model = self.env['res.users']
        location_ids = user_model.get_all_location().ids
        if location_ids:
            return location_ids[0]
        else:
            return super(StockInventory, self)._default_location_id()
        
    #reemplazar campo para cambiar la funcion por defecto
    location_id = fields.Many2one('stock.location', default=_default_location_id)
    #reemplazar campo para cambiar el states, en estado en proceso, debe poder editarse el nombre
    #esto cuando se inicia desde la interfaz de codigos de barras
    #pasa directo a ese estado y no hay como cambiar el nombre
    name = fields.Char(states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    state = fields.Selection(selection_add=[('waiting', 'Esperando aprobación')])
    
    @api.model
    def default_get(self, fields_list):
        values = super(StockInventory, self).default_get(fields_list)
        values['filter'] = 'partial'
        return values
    
    def on_barcode_scanned(self, barcode):
        res = super(StockInventory, self).on_barcode_scanned(barcode)
        for line in self.line_ids:
            if line.product_id and not line.price_unit:
                line.price_unit = line.product_id.standard_price
        return res
    
    @api.multi
    def _action_done(self):
        if not self.env['res.users'].has_group('l10n_cl_stock.group_validate_guias'):
            self.write({'state': 'waiting'})
            return True
        return super(StockInventory, self)._action_done()
    
    @api.model
    def _get_extra_domain(self):
        user_model = self.env['res.users']
        domain = []
        location_ids = []
        if (not user_model.has_group('stock.group_stock_manager') and not user_model.has_group('l10n_cl_stock.group_validate_guias')) \
                and not self.env.context.get('show_all_location',False):
            location_ids = user_model.get_all_location().ids
            if location_ids:
                domain.append(('location_id','in', location_ids))
        return domain
