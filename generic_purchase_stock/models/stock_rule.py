from odoo import models, api, fields, tools


class StockRule(models.Model):
    _inherit = 'stock.rule'
    
    @api.multi
    def _run_buy(self, product_id, product_qty, product_uom, location_id, name, origin, values):
        '''
        Despues de crear el abastecimiento para compras, enviar a recalcular los impuestos en el PO
        '''
        super(StockRule, self)._run_buy(product_id, product_qty, product_uom, location_id, name, origin, values)
        suppliers = product_id.seller_ids\
            .filtered(lambda r: (not r.company_id or r.company_id == values['company_id']) and (not r.product_id or r.product_id == product_id))
        if suppliers:
            supplier = self._make_po_select_supplier(values, suppliers)
            partner = supplier.name    
            domain = self._make_po_get_domain(values, partner)
            po = self.env['purchase.order'].search([dom for dom in domain])
            if po:
                po.compute_taxes()
