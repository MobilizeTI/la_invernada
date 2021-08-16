from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.tools import float_compare
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError, ValidationError


class PurchaseOrder(models.Model):    
    _inherit = "purchase.order"
    _name = "purchase.order"
    
    @api.depends('order_line.price_total', 'tax_ids.amount')
    def _amount_all(self):
        # calcular los datos en base a la nueva clase de impuestos para no recalcularlos cada vez sino tomar lo ya calculado
        amount_untaxed, amount_tax = 0.0, 0.0
        for order in self:
            amount_untaxed, amount_tax = 0.0, 0.0
            cur = order.currency_id
            for line in order.tax_ids:
                amount_tax += line.amount
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
            order.amount_tax = cur.round(amount_tax)
            order.amount_untaxed = cur.round(amount_untaxed)
            order.amount_total = order.amount_untaxed + order.amount_tax
    
    @api.multi
    def _get_key_tax_grouped(self, line):
        # no agrupar por producto, pero en otro modulo quizas sea necesario
        # en Ecuador por ejemplo se deberia agrupar para los productos ICE
        product = False
        tax_key = (False, False, product, line.taxes_id)
        return tax_key
    
    @api.multi
    def get_tax_grouped(self):
        """
        Acumular el subtotal antes de calcular el impuesto
        esto para evitar problemas al calcular el impuesto por linea, al redondear se obtienen datos errados
        acumulando el valor se obtiene mayor precision.
        la acumulacion de valores sera por la cuenta contable, cuenta analitica e impuestos
        solo cuando sea un producto con ICE, agregar el producto para el calculo correcto.
        Para descuentos, no calcular el % de descuento y luego el subtotal restando el % de descuento
        eso trae problemas de descuento, hay que calcular el valor del descuento y eso restarlo al subtotal, ejemplo:
        Cantidad 3, Precio Unit 0,9 Descuento 15%
        ***Erroneo*** 
        Subtotal = 2,7 
        Descuento 0,405(si redondeamos seria 0,41)
        subtotal con descuento 2,7 * 0.85 = 2,295(si redondeamos 2.3)
        ***Correcto***
        Subtotal = 2,7 
        Descuento 0,405(si redondeamos seria 0,41)
        subtotal con descuento 2,7 - 0,41 = 2,29
        *********************************************************
        Con el primer calculo tendriamos una diferencia de 1
        pero el valor correcto seria 2,9 esto se soluciona en el segundo ejemplo
        """
        self.ensure_one()
        default_data = {'subtotal': 0.0, 'discount_total': 0.0, 'quantity_sum': 0.0}
        tax_data = {}
        tax_key = False
        for line in self.order_line:
            tax_key = self._get_key_tax_grouped(line)
            tax_data.setdefault(tax_key, default_data.copy())
            tax_data[tax_key]['discount_total'] += line._get_discount_total()
            tax_data[tax_key]['subtotal'] += (line.price_unit * line.product_qty)
            tax_data[tax_key]['quantity_sum'] += line.product_qty
        return tax_data
    
    tax_ids = fields.One2many('purchase.order.tax', 'order_id', 'Impuestos', readonly=True)

    @api.model
    def create(self, vals):
        order = super(PurchaseOrder, self).create(vals)
        if any(line.taxes_id for line in order.order_line) and not order.tax_ids:
            order.compute_taxes()
        return order
    
    @api.multi
    def _prepare_tax_line_vals(self, tax):
        """ Prepare values to create an purchase.order.tax line
        """
        vals = {
            'order_id': self.id,
            'tax_id': tax['id'],
            'amount': tax['amount'],
            'base': tax['base'],
        }
        return vals
    
    @api.multi
    def get_taxes_values(self):
        tax_grouped = {}
        tax_data = self.get_tax_grouped()
        for (account, account_analytic, product, tax_recs), total_data in tax_data.items():
            discount_total = tools.float_round(total_data['discount_total'], precision_digits=self.currency_id.decimal_places)
            subtotal = tools.float_round(total_data['subtotal'], precision_digits=self.currency_id.decimal_places)
            values = tax_recs.compute_all(subtotal - discount_total, quantity=1, product=product, partner=self.partner_id)
            for tax in values['taxes']:
                val = self._prepare_tax_line_vals(tax)
                key = tax['id'] #agrupar por impuesto
                if key not in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
        for val in tax_grouped.values():
            val['amount'] = tools.float_round(val['amount'], precision_digits=self.currency_id.decimal_places)
            val['base'] = tools.float_round(val['base'], precision_digits=self.currency_id.decimal_places)
        return tax_grouped
    
    @api.multi
    def compute_taxes(self):
        """Function used in other module to compute the taxes on a fresh sale order created (onchanges did not applied)"""
        purchase_order_tax = self.env['purchase.order.tax']
        for order in self:
            # Delete non-manual tax lines
            self._cr.execute("DELETE FROM purchase_order_tax WHERE order_id=%s ", (order.id,))
            self.invalidate_cache()
            # Generate one tax line per tax, however many invoice lines it's applied to
            tax_grouped = order.get_taxes_values()
            # Create new tax lines
            for tax in tax_grouped.values():
                purchase_order_tax.create(tax)
        return True
    
    @api.onchange('order_line')
    def _onchange_lines(self):
        taxes_grouped = self.get_taxes_values()
        tax_lines = self.env['purchase.order.tax'].browse()
        for tax in taxes_grouped.values():
            tax_lines += tax_lines.new(tax)
        self.tax_ids = tax_lines
        return
     
    @api.multi
    def button_confirm(self):
        messages = []
        for order in self:
            messages = []
            for line in order.order_line.filtered(lambda x: not x.taxes_id):
                messages.append("Producto: %s" % (line.name))
            if messages:
                raise UserError("Hay Lineas que no tienen impuestos, por favor verifique y asigne el impuesto correcto.\n %s" % 
                                ("\n".join(messages)))
            if any(line.taxes_id for line in order.order_line) and not order.tax_ids:
                order.compute_taxes()
        res = super(PurchaseOrder, self).button_confirm()
        return res
    
    @api.multi
    def _get_report_base_filename(self):
        report_name = "Pedido de Compra %s" % self.name
        if self.state in ('draft', 'sent'):
            report_name = "Solicitud de Presupuesto %s" % self.name
        return report_name
    
    @api.multi
    def _add_supplier_to_product(self):
        #hacer la llamada super, xq el usuario de compras no tiene permisos para crear tarifas de compra por proveedor
        return super(PurchaseOrder, self.sudo())._add_supplier_to_product()

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"
    
    discount = fields.Float(string='Descuento (%)', digits=dp.get_precision('Discount'), default=0.0)
    # campo para dar soporte a descuentos en monto y no solo en porcentaje
    # este campo deber tener preferencia sobre el descuento en %
    discount_value = fields.Float('Descuento(monto)', 
        digits=dp.get_precision('Product Price'))
    price_unit_final = fields.Float('Precio Unitario Final', 
        digits=dp.get_precision('Product Price'), 
        compute='_compute_price_unit_final', store=True)
    
    _sql_constraints = [
        ('discount_limit', 'CHECK (discount <= 100.0)', 'El Descuento debe estar entre 0 y 100, por favor verifique.'),
    ]
    
    @api.depends('price_unit','product_id','discount', 'discount_value')
    def _compute_price_unit_final(self):
        for line in self:
            line.price_unit_final = line._get_price_unit_final()
            
    @api.depends('price_unit', 'product_id', 'product_qty', 'discount', 'discount_value', 'taxes_id')
    def _compute_amount(self):
        super(PurchaseOrderLine, self)._compute_amount()
    
    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        warning = {}
        if self.product_uom.category_id != self.product_id.uom_id.category_id:
            self.product_uom = self.product_id.uom_id.id
            warning = {
                'title': "Informacion para el usuario",
                'message': "La unidad de medida seleccionada debe pertenecer a la misma categoria"\
                    " que la Unidad de medida del producto: %s" % self.product_id.uom_id.category_id.name
            }
        res = super(PurchaseOrderLine, self)._onchange_quantity()
        if not res:
            res = {}
        res['warning'] = warning
        res['domain'] = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        return res
    
    @api.onchange('discount')
    def _onchange_discount(self):
        self.discount_value = 0
    
    @api.multi
    def _get_discount_total(self):
        return (self.discount_value * self.product_qty) or (self.price_unit * self.product_qty * self.discount * 0.01)
    
    @api.multi
    def _get_discount_unit(self):
        return self.discount_value or (self.price_unit * self.discount * 0.01)
    
    @api.multi
    def _get_price_unit_final(self):
        # funcion generica para pasar el precio unitario restando el descuento
        currency = self.order_id.currency_id
        discount_total = tools.float_round(self._get_discount_unit(), precision_digits=currency.decimal_places)
        price_unit_final = self.price_unit - discount_total
        return price_unit_final
    
    def _prepare_compute_all_values(self):
        vals = super(PurchaseOrderLine, self)._prepare_compute_all_values()
        currency = self.order_id.currency_id
        # calcular el descuento y al neto restarle el descuento, para evitar problemas de redondeo
        # no calcular el % de descuento nuevamente
        discount_total = tools.float_round(self._get_discount_total(), precision_digits=currency.decimal_places)
        subtotal = tools.float_round(self.price_unit * self.product_qty, precision_digits=currency.decimal_places)
        vals['price_unit'] = subtotal - discount_total
        vals['product_qty'] = 1
        return vals


class PurchaseOrderTax(models.Model):    
    _inherit = "common.document.tax"
    _name = 'purchase.order.tax'

    order_id = fields.Many2one('purchase.order', string='Orden', ondelete='cascade', index=True)
