from collections import OrderedDict
from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class StockInventory(models.Model):
    _inherit = 'stock.inventory'
    
    @api.model
    def create(self, vals):
        new_rec = super(StockInventory, self).create(vals)
        self.env['pos.config'].notify_adjustment_updates()
        return new_rec
    
    @api.multi
    def write(self, vals):
        res = super(StockInventory, self).write(vals)
        self.env['pos.config'].notify_adjustment_updates()
        return res
    
    @api.multi
    def unlink(self):
        res = super(StockInventory, self).unlink()
        self.env['pos.config'].notify_adjustment_updates()
        return res

    @api.model
    def _get_extra_domain(self):
        user_model = self.env['res.users']
        domain = []
        #al cargar inventario desde el pos, si no tiene el grupo de usuario de inventario no cargar ningun inventario
        #para q no se muestren los botones a usuarios no autorizados
        if self.env.context.get('inventory_from_pos') and not user_model.has_group('stock.group_stock_user'):
            domain.append(('id','<', 0))
        return domain
    
    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        args.extend(self._get_extra_domain())
        res = super(StockInventory, self)._search(args=args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
        return res
    
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        domain.extend(self._get_extra_domain())
        res = super(StockInventory, self).read_group(domain=domain, fields=fields, groupby=groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return res
    
    @api.model
    def _find_inventory_from_pos(self, inventory_id):
        return self.search([('id', '=', inventory_id)], limit=1)
    
    @api.multi
    def _is_line_valid_from_pos(self, product, vals_line_pos):
        """
        Verificar si el producto pertenece al inventario
        se puede personalizar en modulos, para permitir ciertos productos en base a cierta configuracion
        """
        return True
    
    @api.multi
    def _get_domain_for_products_to_zero(self):
        """
        Cuando se hace inventario de las lineas especificadas en el pos
        adicional se puede agregar las lineas que no se especificaron en el pos
        con cantidad 0, en base a este domain se buscara los producto que se establezcan a 0
        esta funcion se crea con el fin de usarla en otros modulos
        """
        return []
    
    @api.multi
    def _prepare_inventory_line_from_pos(self, product, vals_line_pos):
        line_vals = {
            'inventory_id': self.id,
            'product_id': product.id,
            'product_qty': vals_line_pos.get('qty') or 0,
            'location_id': self.location_id.id,
        }
        return line_vals
    
    @api.multi
    def _prepare_inventory_line_zero(self, product, vals_line_pos):
        line_vals = self._prepare_inventory_line_from_pos(product, vals_line_pos)
        line_vals['product_qty'] = 0
        return line_vals
    
    @api.multi
    def _create_inventory_line_from_pos(self, product, vals_line):
        inventory_line_model = self.env['stock.inventory.line']
        line_rec = inventory_line_model.new(vals_line)
        line_rec._onchange_product()
        line_vals = inventory_line_model._convert_to_write({name: line_rec[name] for name in line_rec._cache})
        return inventory_line_model.create(line_vals)
        
    @api.model
    def set_inventory_from_ui(self, inventory_lines, inventory_id):
        product_model = self.env['product.product']
        inventory = self._find_inventory_from_pos(inventory_id)
        #borrar las lineas existentes en caso de existir
        if inventory.line_ids:
            inventory.line_ids.sudo().unlink()
        line_vals = {}
        product_ids = []
        product_ok = True
        real_inventory_lines = OrderedDict()
        line_key = False
        for line in inventory_lines:
            line_key = (line.get('product_id'),)
            if line_key in real_inventory_lines:
                real_inventory_lines[line_key]['qty'] += line.get('qty') or 0
            else:
                real_inventory_lines[line_key] = line.copy()
        for line in real_inventory_lines.values():
            product = product_model.browse(line['product_id'])
            product_ok = inventory._is_line_valid_from_pos(product, line)
            if not product_ok:
                continue
            product_ids.append(line['product_id'])
            line_vals = inventory._prepare_inventory_line_from_pos(product, line)
            inventory._create_inventory_line_from_pos(product, line_vals)
        domain = inventory._get_domain_for_products_to_zero()
        if domain:
            if product_ids:
                domain.append(('id','not in', product_ids))
            products = self.env['product.product'].search(domain)
            #los productos no inventariados, pasarlos con cantidad 0 para ajustar el inventario
            for product in products:
                line_vals = inventory._prepare_inventory_line_zero(product, {})
                inventory._create_inventory_line_from_pos(product, line_vals)
        inventory._action_done()
        return (inventory.id, inventory.display_name)
