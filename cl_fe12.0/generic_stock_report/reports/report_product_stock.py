from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo import tools


class ReportProductStock(models.Model):    
    _name = 'report.product.stock'
    _description = 'Analisis de Stock de Productos'
    _auto = False
    
    product_id = fields.Many2one('product.product', string='Producto', readonly=True)
    product_template_id = fields.Many2one('product.template', string='Plantilla de Producto', readonly=True)
    product_categ_id = fields.Many2one('product.category', string='Categoria de producto', readonly=True)
    location_id = fields.Many2one('stock.location', 'Bodega', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    qty_available = fields.Integer(string='Stock Actual', digits=dp.get_precision('Product Unit of Measure'), readonly=True)
    virtual_available = fields.Integer(string='Stock Virtual', digits=dp.get_precision('Product Unit of Measure'), readonly=True)
    incoming_qty = fields.Integer(string='Stock Entrante', digits=dp.get_precision('Product Unit of Measure'), readonly=True)
    outgoing_qty = fields.Integer(string='Stock Saliente', digits=dp.get_precision('Product Unit of Measure'), readonly=True)

    def _select(self):
        select_str = """
            SELECT
                CONCAT(p.id, stock.location_id) AS id,
                stock.*,
                pt.id AS product_template_id,
                pt.categ_id AS product_categ_id
        """
        return select_str
    
    def _sub_select(self):
        sub_select_str = """
            SELECT 
                product_id,
                location_id,
                company_id,
                COALESCE(SUM(report.qty_available),0) AS qty_available,
                COALESCE(SUM(report.qty_available),0) + COALESCE(SUM(report.incoming),0) - COALESCE(SUM(report.outgoing),0) AS virtual_available,
                COALESCE(SUM(incoming)) AS incoming_qty, 
                COALESCE(SUM(outgoing)) AS outgoing_qty
            FROM (SELECT 
                product_stock_available.product_id, 
                product_stock_available.location_id, 
                product_stock_available.company_id,
                SUM(qty) AS qty_available,
                0 AS incoming, 0 AS outgoing
                FROM (
                    SELECT 
                        sm.product_id AS product_id,
                        sm.location_dest_id AS location_id,
                        sm.company_id AS company_id,
                        SUM(sm.product_qty) AS qty
                    FROM stock_move sm
                    WHERE sm.state = 'done'
                    GROUP BY sm.product_id, sm.location_dest_id, sm.company_id
                    UNION ALL
                    SELECT
                        sm.product_id AS product_id,
                        sm.location_id AS location_id,
                        sm.company_id AS company_id,
                        -SUM(sm.product_qty) AS qty
                    FROM stock_move sm
                    WHERE sm.state = 'done'
                    GROUP BY sm.product_id, sm.location_id, sm.company_id
                ) AS product_stock_available 
                GROUP BY product_stock_available.product_id, product_stock_available.location_id, product_stock_available.company_id
                UNION ALL
                    SELECT 
                        prod AS product_id, 
                        stock_in_out_data.location_id,
                        stock_in_out_data.company_id,
                        0 as qty_available,
                        SUM(stock_in_out_data.in) AS incoming,
                        SUM(stock_in_out_data.out) AS outgoing
                    FROM
                        (SELECT 
                            sm.product_id AS prod,
                            sm.location_dest_id AS location_id,
                            sm.company_id AS company_id,
                            SUM(product_qty) AS in,
                            0 as out
                        FROM stock_move sm
                        WHERE sm.state IN ('confirmed', 'waiting', 'assigned')
                            GROUP BY sm.product_id, sm.location_dest_id, sm.company_id
                        UNION
                        SELECT
                            sm.product_id AS prod, 
                            sm.location_id AS location_id,
                            sm.company_id AS company_id,
                            0 AS in, 
                            SUM(product_qty) AS out 
                        FROM stock_move sm
                        WHERE sm.state IN ('confirmed', 'waiting', 'assigned')
                        GROUP BY sm.product_id, sm.location_id, sm.company_id
                        ) AS stock_in_out_data
                    GROUP BY prod, stock_in_out_data.location_id, stock_in_out_data.company_id
                ) report GROUP BY product_id, location_id, company_id
        """
        return sub_select_str
    
    def _from(self):
        from_str = """
            product_product p
                INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
                LEFT JOIN 
                    (
                    %s
                )  stock ON (P.id = stock.product_id)
                INNER JOIN stock_location sl ON sl.id = stock.location_id
        """
        return from_str % (self._sub_select())
    
    def _where(self):
        where_str = """
            sl.usage = 'internal'
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
