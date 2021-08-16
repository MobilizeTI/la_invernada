from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo import tools


class ReportPurchaseStock(models.Model):    
    _name = 'report.purchase.stock'
    _description = 'Analisis de Compra de productos'
    _auto = False
    
    warehouse_id = fields.Many2one('stock.warehouse', 'Tienda', readonly=True)
    product_id = fields.Many2one('product.product', 'Producto', readonly=True)
    product_template_id = fields.Many2one('product.template', 'Plantilla de Producto', readonly=True)
    product_categ_id = fields.Many2one('product.category', string='Categoria de producto', readonly=True)
    purchase_qty = fields.Integer(string='Cantidad a comprar', digits=dp.get_precision('Product Unit of Measure'), readonly=True)
    qty_available = fields.Integer(string='Stock Actual', digits=dp.get_precision('Product Unit of Measure'), readonly=True)
    qty_in = fields.Integer(string='Stock Entrante', digits=dp.get_precision('Product Unit of Measure'), readonly=True)
    qty_out = fields.Integer(string='Stock Saliente', digits=dp.get_precision('Product Unit of Measure'), readonly=True)
    
    def _select(self):
        select_str = """
            SELECT
                CONCAT(p.id, sw.id) AS id,
                p.id AS product_id,
                sw.id AS warehouse_id,
                pt.id AS product_template_id,
                pt.categ_id AS product_categ_id,
                product_data.purchase_qty,
                product_data.qty_available,
                product_data.qty_in,
                product_data.qty_out
        """
        return select_str
    
    def _sub_select(self):
        sub_select_str = """
            SELECT sub.product_id,
                sub.warehouse_id,
                SUM(sub.purchase_qty) AS purchase_qty,
                SUM(sub.qty_available) AS qty_available,
                SUM(sub.qty_in) AS qty_in,
                SUM(sub.qty_out) AS qty_out
            FROM (
                --compras pendientes
                SELECT pl.product_id AS product_id,
                    SUM(pl.product_qty/u.factor*u2.factor) AS purchase_qty,
                    0 AS qty_available,
                    0 AS qty_in,
                    0 AS qty_out,
                    spt.warehouse_id
                FROM purchase_order_line pl
                    join purchase_order s on (pl.order_id=s.id)
                    left join product_product p on (pl.product_id=p.id)
                    left join product_template t on (p.product_tmpl_id=t.id)
                    left join uom_uom u on (u.id=pl.product_uom)
                    left join uom_uom u2 on (u2.id=t.uom_id)
                    left join stock_picking_type spt on (spt.id=s.picking_type_id)
                WHERE s.state NOT IN ('purchase','done', 'cancel')
                GROUP BY pl.product_id, spt.warehouse_id
                --stock disponible
                UNION ALL 
                SELECT sq.product_id AS product_id,
                    0 AS purchase_qty,
                    SUM(sq.quantity) AS qty_available,
                    0 AS qty_in,
                    0 AS qty_out,
                    sw.id AS warehouse_id
                FROM stock_quant sq
                    INNER JOIN stock_warehouse sw ON sw.lot_stock_id = sq.location_id
                GROUP BY sq.product_id, sw.id
                --cantidad entrante 
                UNION ALL 
                SELECT sm.product_id AS product_id,
                    0 AS purchase_qty,
                    0 AS qty_available,
                    SUM(sm.product_qty) AS qty_in,
                    0 AS qty_out,
                    sw.id AS warehouse_id
                FROM stock_move sm
                    INNER JOIN stock_warehouse sw ON (sw.lot_stock_id = sm.location_dest_id AND sw.lot_stock_id != sm.location_id)
                WHERE sm.state NOT IN ('draft','done', 'cancel')
                GROUP BY sm.product_id, sw.id
                --cantidad saliente
                UNION ALL 
                SELECT sm.product_id AS product_id,
                    0 AS purchase_qty,
                    0 AS qty_available,
                    0 AS qty_in,
                    SUM(sm.product_qty) AS qty_out,
                    sw.id AS warehouse_id
                FROM stock_move sm
                    INNER JOIN stock_warehouse sw ON (sw.lot_stock_id = sm.location_id AND sw.lot_stock_id != sm.location_dest_id)
                WHERE sm.state NOT IN ('draft','done', 'cancel')
                GROUP BY sm.product_id, sw.id 
                ) AS sub
            GROUP BY sub.product_id, sub.warehouse_id
        """
        return sub_select_str
    
    def _from(self):
        from_str = """
            stock_warehouse sw
                INNER JOIN 
                    (
                    %s
                ) AS product_data ON product_data.warehouse_id = sw.id
                INNER JOIN product_product p ON p.id = product_data.product_id
                INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
        """
        return from_str % (self._sub_select())
    
    def _where(self):
        where_str = """
            pt.type != 'service'
        """
        return where_str
    
    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            WHERE %s
        )""" % (self._table, self._select(), self._from(), self._where()))
