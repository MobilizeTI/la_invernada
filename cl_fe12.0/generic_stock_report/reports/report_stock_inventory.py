from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo import tools


class ReportStockInventory(models.Model):    
    _name = 'report.stock.inventory'
    _description = 'Analisis de Ajustes de inventario'
    _auto = False
    _rec_name = 'inventory_id' 
    
    inventory_id = fields.Many2one('stock.inventory', 'Ajuste de Inventario', readonly=True)
    company_id = fields.Many2one('res.company', 'Compañia', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Propietario', readonly=True)
    package_id = fields.Many2one('stock.quant.package', 'Paquete', readonly=True)
    prod_lot_id = fields.Many2one('stock.production.lot', 'Numero de Serie/Lote', readonly=True)
    location_id = fields.Many2one('stock.location', 'Bodega', readonly=True)
    product_id = fields.Many2one('product.product', 'Producto', readonly=True)
    product_template_id = fields.Many2one('product.template', 'Plantilla de Producto', readonly=True)
    product_categ_id = fields.Many2one('product.category', 'Categoria de Producto', readonly=True)
    product_uom_id = fields.Many2one('uom.uom', 'UdM', readonly=True)
    product_qty = fields.Float('Cantidad Real', digits=dp.get_precision('Product Unit of Measure'), readonly=True)
    theoretical_qty = fields.Float('Cantidad Teorica', digits=dp.get_precision('Product Unit of Measure'), readonly=True)
    diff_qty = fields.Float('Cantidad de Ajuste', digits=dp.get_precision('Product Unit of Measure'), readonly=True)
    price_unit = fields.Float('Precio Unitario', digits=dp.get_precision('Product Price'), group_operator="avg", readonly=True)
    price_subtotal = fields.Float('Costo Total', digits=dp.get_precision('Account'), readonly=True)
    date = fields.Datetime('Fecha de Inventario', readonly=True)
    state = fields.Selection(string='Estado', selection=[
        ('draft', 'Borrador'),
        ('cancel', 'Cancelado'),
        ('confirm', 'En Proceso'),
        ('done', 'Validado')],
        readonly=True)
    
    def _select(self):
        select_str = """
            SELECT
                l.id AS id,
                si.state,
                si.date,
                date_part('month', si.date AT TIME ZONE 'UTC') AS month,
                si.id AS inventory_id,
                si.company_id,
                l.partner_id,
                l.package_id,
                l.prod_lot_id,
                l.location_id,
                l.product_id,
                l.product_uom_id,
                COALESCE(l.product_qty, 0) AS product_qty,
                COALESCE(l.theoretical_qty, 0) AS theoretical_qty,
                (COALESCE(l.product_qty, 0) - COALESCE(l.theoretical_qty, 0)) AS diff_qty,
                l.price_unit,
                ((COALESCE(l.product_qty, 0) - COALESCE(l.theoretical_qty, 0)) * l.price_unit) AS price_subtotal,
                pt.id AS product_template_id,
                pt.categ_id AS product_categ_id
        """
        return select_str
    
    def _from(self):
        from_str = """
            stock_inventory_line l
                INNER JOIN stock_inventory si ON si.id = l.inventory_id
                LEFT JOIN product_product p ON (l.product_id=p.id)
                LEFT JOIN product_template pt ON (p.product_tmpl_id=pt.id)
        """
        return from_str
    
    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
        )""" % (self._table, self._select(), self._from()))
