from odoo import models, api, fields, tools
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import safe_eval as eval 
import odoo.addons.decimal_precision as dp

class SaleOrder(models.Model):
    _inherit = 'sale.order'

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
        tax_key = (False, False, product, line.tax_id)
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
            tax_data[tax_key]['subtotal'] += (line.price_unit * line.product_uom_qty)
            tax_data[tax_key]['quantity_sum'] += line.product_uom_qty
        return tax_data
    
    tax_ids = fields.One2many('sale.order.tax', 'order_id', 'Impuestos', readonly=True)
    
    @api.model
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        if any(line.tax_id for line in order.order_line) and not order.tax_ids:
            order.compute_taxes()
        return order
    
    @api.multi
    def _prepare_tax_line_vals(self, tax):
        """ Prepare values to create an sale.order.tax line
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
        sale_order_tax = self.env['sale.order.tax']
        for order in self:
            # Delete non-manual tax lines
            self._cr.execute("DELETE FROM sale_order_tax WHERE order_id=%s ", (order.id,))
            self.invalidate_cache()
            # Generate one tax line per tax, however many invoice lines it's applied to
            tax_grouped = order.get_taxes_values()
            # Create new tax lines
            if tax_grouped:
                for tax in tax_grouped.values():
                    sale_order_tax.create(tax)
            else:
                order._amount_all()
        return True
    
    @api.onchange('order_line')
    def _onchange_lines(self):
        taxes_grouped = self.get_taxes_values()

        tax_lines = self.env['sale.order.tax'].browse()
        for tax in taxes_grouped.values():
            tax_lines += tax_lines.new(tax)

        self.tax_ids = tax_lines
        return

    @api.multi
    def action_confirm(self):
        messages = []
        for order in self:
            messages = []
            for line in order.order_line.filtered(lambda x: not x.tax_id and not x.display_type):
                messages.append("Producto: %s" % (line.name))
            if messages:
                raise UserError("Hay Lineas que no tienen impuestos, por favor verifique y asigne el impuesto correcto.\n %s" % 
                                ("\n".join(messages)))
        res = super(SaleOrder, self).action_confirm()
        return res

    @api.multi
    def action_cancel(self):
        for invoice in self.mapped('invoice_ids'):
            if invoice.state in ('open', 'paid'):
                raise UserError("No puede cancelar este pedido, ya hay facturas realizadas, intente cancelarlas primero")
        self.mapped('invoice_ids').action_cancel()
        return super(SaleOrder, self).action_cancel()
    
    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        invoice_model = self.env['account.invoice']
        invoice_ids = []
        new_invoice_ids = super(SaleOrder, self).action_invoice_create(grouped, final)
        if new_invoice_ids:
            invoice_ids.extend(new_invoice_ids)
            for invoice_to_split_id in new_invoice_ids:
                while invoice_to_split_id:
                    invoice_to_split_id = invoice_model.split_invoice_document(invoice_to_split_id)
                    #pasarla a la lista de facturas creadas, para mostrarlas desde el asistente de ser necesario
                    if invoice_to_split_id and invoice_to_split_id not in invoice_ids:
                        invoice_ids.append(invoice_to_split_id)
        return invoice_ids
    
    @api.multi
    def action_view_invoice(self):
        res = super(SaleOrder, self).action_view_invoice()
        try:
            ctx = eval(res.get('context') or {}) 
            ctx['search_default_this_month'] = False
            res['context'] = ctx
        except:
            pass
        return res

    @api.model
    def action_translate_terms(self):
        team_sale_traductions = self.env['ir.translation'].search([('name','=','crm.team,name')])
        for team_sale_traduction in team_sale_traductions:
            if team_sale_traduction.source == 'Sales':
                team_sale_traduction.write({'value': 'Ventas Directas'})
        return True

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    # campo para dar soporte a descuentos en monto y no solo en porcentaje
    # este campo deber tener preferencia sobre el descuento en %
    discount_value = fields.Float('Descuento(monto)', 
        digits=dp.get_precision('Product Price'))
    
    @api.depends('product_uom_qty', 'discount', 'discount_value', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            currency = line.order_id.currency_id
            discount_total = tools.float_round(line._get_discount_total(), precision_digits=currency.decimal_places)
            subtotal = tools.float_round(line.price_unit * line.product_uom_qty, precision_digits=currency.decimal_places)
            taxes = line.tax_id.compute_all(subtotal - discount_total, line.order_id.currency_id, 1, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
            
    @api.onchange('discount')
    def _onchange_discount(self):
        self.discount_value = 0
    
    @api.multi
    def _get_discount_total(self):
        return (self.discount_value * self.product_uom_qty) or (self.price_unit * self.product_uom_qty * self.discount * 0.01)
    
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
    
    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        res = {}
        if self.product_id and self.product_uom:
            if self.product_uom.category_id != self.product_id.uom_id.category_id:
                self.product_uom = self.product_id.uom_id.id
                warning = {'title': "Informacion para el usuario",
                           'message': "La unidad de medida seleccionada debe pertenecer a la misma categoria "\
                                        "que la Unidad de medida del producto: %s" % self.product_id.uom_id.category_id.name
                           }
                res['warning'] = warning
                res.setdefault('domain', {}).setdefault('product_uom', []).append(('category_id', '=', self.product_id.uom_id.category_id.id))
                return res
        res = super(SaleOrderLine, self).product_uom_change()
        if self.product_id:
            if not res:
                res = {}
            res.setdefault('domain', {}).setdefault('product_uom', []).append(('category_id', '=', self.product_id.uom_id.category_id.id))
        return res
    
    @api.multi
    def _prepare_invoice_line(self, qty):
        vals = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        vals['discount_value'] = self.discount_value
        return vals


class SaleOrderTax(models.Model):
    
    _inherit = "common.document.tax"
    _name = 'sale.order.tax'

    order_id = fields.Many2one('sale.order', string='Orden', ondelete='cascade', index=True)
