from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp


class PurchaseReport(models.Model):    
    _inherit = "purchase.report"
    
    discount = fields.Float(string='Descuento (%)', digits=dp.get_precision('Discount'), default=0.0, group_operator="avg")
    total_descuento = fields.Float('Descuento(Monto)', 
        readonly=True, digits=dp.get_precision('Account'))
    price_subtotal = fields.Float(string='Subtotal', digits=dp.get_precision('Account'))
    price_tax = fields.Float(string='Impuestos', digits=dp.get_precision('Account'))
    qty_invoiced = fields.Float(string="Cantidad Facturada", digits=dp.get_precision('Product Unit of Measure'))
    qty_received = fields.Float(string="Cantidad Recibida", digits=dp.get_precision('Product Unit of Measure'))

    def _select(self):
        select = super(PurchaseReport, self)._select()
        select = select.replace(
            "sum(l.price_unit / COALESCE(NULLIF(cr.rate, 0), 1.0) * l.product_qty)::decimal(16,2) as price_total,", 
            "sum(l.price_total) AS price_total,"
        )
        select = select.replace(
            "avg(100.0 * (l.price_unit / COALESCE(NULLIF(cr.rate, 0),1.0) * l.product_qty) / NULLIF(ip.value_float*l.product_qty/u.factor*u2.factor, 0.0))::decimal(16,2) as negociation,",
            "avg(100.0 * (l.price_unit_final / COALESCE(NULLIF(cr.rate, 0),1.0) * l.product_qty) / NULLIF(ip.value_float*l.product_qty/u.factor*u2.factor, 0.0))::decimal(16,2) as negociation,"
        )
        select = select.replace(
            "(sum(l.product_qty * l.price_unit / COALESCE(NULLIF(cr.rate, 0), 1.0))/NULLIF(sum(l.product_qty/u.factor*u2.factor),0.0))::decimal(16,2) as price_average,",
            "(sum(l.product_qty * l.price_unit_final / COALESCE(NULLIF(cr.rate, 0), 1.0))/NULLIF(sum(l.product_qty/u.factor*u2.factor),0.0))::decimal(16,2) as price_average,"
        )
        select += """ , AVG(l.discount) AS discount, SUM(CASE WHEN COALESCE(l.discount_value, 0) > 0 THEN l.discount_value * l.product_qty ELSE (l.price_unit * l.product_qty * l.discount * 0.01) END) AS total_descuento, SUM(l.price_subtotal) AS price_subtotal, SUM(l.price_tax) AS price_tax """
        select += """ , SUM(l.qty_invoiced) AS qty_invoiced, SUM(l.qty_received) AS qty_received """
        return select  