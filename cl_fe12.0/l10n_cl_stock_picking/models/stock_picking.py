# -*- coding: utf-8 -*-
from odoo import osv, models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import except_orm, UserError
import odoo.addons.decimal_precision as dp
from odoo.tools.float_utils import float_compare, float_round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import logging
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.onchange('currency_id', 'move_lines.subtotal', 'move_reason')
    def _compute_amount(self):
        for rec in self:
            logging.info("PRUEBAAAAAAAAA")
            amount_untaxed = 0
            amount_total = 0
            if rec.move_reason not in ['5']:
                taxes = {}
                for move in rec.move_lines:
                    amount_untaxed += move.price_untaxed 
                    logging.info(move.subtotal)
                    logging.info(move.price_untaxed )
                    amount_total += move.subtotal

                rec.amount_tax = round((19*amount_total)/100,2)

                
                rec.amount_untaxed = amount_total
            rec.amount_total = round((19*amount_total)/100,2) + amount_total

    def _prepare_tax_line_vals(self, line, tax):
        """ Prepare values to create an account.invoice.tax line

        The line parameter is an account.invoice.line, and the
        tax parameter is the output of account.tax.compute_all().
        """
        t = self.env['account.tax'].browse(tax['id'])
        vals = {
            'picking_id': self.id,
            'description': t.with_context(**{'lang': self.partner_id.lang} if self.partner_id else {}).description,
            'tax_id': tax['id'],
            'amount': self.currency_id.round(tax['amount'] if tax['amount'] > 0 else (tax['amount'] * -1)),
            'base': tax['base'],
            'manual': False,
            'sequence': tax['sequence'],
            'amount_retencion': tax['retencion']
        }
        return vals

    def get_grouping_key(self, vals):
        return str(vals['tax_id'])

    def _get_grouped_taxes(self, line, taxes, tax_grouped={}):
        for tax in taxes:
            val = self._prepare_tax_line_vals(line, tax)
            key = self.get_grouping_key(val)
            if key not in tax_grouped:
                tax_grouped[key] = val
            else:
                tax_grouped[key]['amount'] += val['amount']
                tax_grouped[key]['amount_retencion'] += val['amount_retencion']
                tax_grouped[key]['base'] += val['base']
        return tax_grouped

    @api.multi
    def get_taxes_values(self):
        tax_grouped = {}
        totales = {}
        included = False
        for line in self.move_lines:
            qty = line.quantity_done
            if qty <= 0:
                qty = line.product_uom_qty
            if (line.move_line_tax_ids and line.move_line_tax_ids[0].price_include) :# se asume todos losproductos vienen con precio incluido o no ( no hay mixes)
                if included or not tax_grouped:#genero error en caso de contenido mixto, en caso primer impusto no incluido segundo impuesto incluido
                    for t in line.move_line_tax_ids:
                        if t not in totales:
                            totales[t] = 0
                        amount_line = (self.currency_id.round(line.precio_unitario *qty))
                        totales[t] += (amount_line * (1 - (line.discount / 100)))
                included = True
            else:
                included = False
            if (totales and not included) or (included and not totales):
                raise UserError('No se puede hacer timbrado mixto, todos los impuestos en este pedido deben ser uno de estos dos:  1.- precio incluído, 2.-  precio sin incluir')
            taxes = line.move_line_tax_ids.with_context(
                date=self.scheduled_date,
                currency=self.currency_id.code).compute_all(line.precio_unitario, self.currency_id, qty, line.product_id, self.partner_id, discount=line.discount, uom_id=line.product_uom)['taxes']
            tax_grouped = self._get_grouped_taxes(line, taxes, tax_grouped)
        #if totales:
        #    tax_grouped = {}
        #    for line in self.invoice_line_ids:
        #        for t in line.invoice_line_tax_ids:
        #            taxes = t.compute_all(totales[t], self.currency_id, 1)['taxes']
        #            tax_grouped = self._get_grouped_taxes(line, taxes, tax_grouped)
        #_logger.warning(tax_grouped)
        '''
        @TODO GDR para guías
        if not self.global_descuentos_recargos:
            return tax_grouped
        gdr, gdr_exe = self.porcentaje_dr()
        taxes = {}
        for t, group in tax_grouped.items():
            if t not in taxes:
                taxes[t] = group
            tax = self.env['account.tax'].browse(group['tax_id'])
            if tax.amount > 0:
                taxes[t]['amount'] *= gdr
                taxes[t]['base'] *= gdr
            else:
                taxes[t]['amount'] *= gdr_exe
        '''
        return tax_grouped

    def set_use_document(self):
        return (self.picking_type_id and self.picking_type_id.code != 'incoming')

    amount_untaxed = fields.Monetary(
            compute='_compute_amount',
            digits=dp.get_precision('Account'),
            string='Untaxed Amount',
        )
    amount_tax = fields.Monetary(
            compute='_compute_amount',
            string='Taxes',
        )
    amount_total = fields.Monetary(
            compute='_compute_amount',
            string='Total',
        )
    currency_id = fields.Many2one(
            'res.currency',
            string='Currency',
            required=True,
            states={'draft': [('readonly', False)]},
            default=lambda self: self.env.user.company_id.currency_id.id,
            track_visibility='always',
        )
    sii_batch_number = fields.Integer(
            copy=False,
            string='Batch Number',
            readonly=True,
            help='Batch number for processing multiple invoices together',
        )
    activity_description = fields.Many2one(
            'sii.activity.description',
            string='Giro',
            related="partner_id.commercial_partner_id.activity_description",
            readonly=True, states={'assigned':[('readonly',False)],'draft':[('readonly',False)]},
        )
    sii_document_number = fields.Char(
            string='Document Number',
            copy=False,
            readonly=True,
        )
    responsability_id = fields.Many2one(
            'sii.responsability',
            string='Responsability',
            related='partner_id.commercial_partner_id.responsability_id',
            store=True, compute_sudo=True,
        )
    next_number = fields.Integer(
            related='picking_type_id.sequence_id.number_next_actual',
            string='Next Document Number',
            readonly=True,
        )
    use_documents = fields.Boolean(
            string='Use Documents?',
            default=set_use_document,
        )
    reference = fields.One2many(
            'stock.picking.referencias',
            'stock_picking_id',
            readonly=False,
            states={'done':[('readonly',True)]},
        )
    transport_type = fields.Selection(
            [
                ('2', 'Despacho por cuenta de empresa'),
                ('1', 'Despacho por cuenta del cliente'),
                ('3', 'Despacho Externo'),
                ('0', 'Sin Definir')
            ],
            string="Tipo de Despacho",
            default="2",
            readonly=False, states={'done':[('readonly',True)]},
        )
    move_reason = fields.Selection(
            [
                    ('1', 'Operación constituye venta'),
                    ('2', 'Ventas por efectuar'),
                    ('3', 'Consignaciones'),
                    ('4', 'Entrega Gratuita'),
                    ('5', 'Traslados Internos'),
                    ('6', 'Otros traslados no venta'),
                    ('7', 'Guía de Devolución'),
                    ('8', 'Traslado para exportación'),
                    ('9', 'Ventas para exportación')
            ],
            string='Razón del traslado',
            default="1",
            readonly=False, states={'done':[('readonly',True)]},
        )
    vehicle = fields.Many2one(
            'fleet.vehicle',
            string="Vehículo",
            readonly=False,
            states={'done': [('readonly', True)]},
        )
    chofer = fields.Many2one(
            'res.partner',
            string="Chofer",
            readonly=False,
            states={'done': [('readonly', True)]},
        )
    patente = fields.Char(
            string="Patente",
            readonly=False,
            states={'done': [('readonly', True)]},
        )
    contact_id = fields.Many2one(
            'res.partner',
            string="Contacto",
            readonly=False,
            states={'done': [('readonly', True)]},
        )
    invoiced = fields.Boolean(
            string='Invoiced?',
            readonly=True,
        )
    respuesta_ids = fields.Many2many(
            'sii.respuesta.cliente',
            string="Recepción del Cliente",
            readonly=True,
        )

    @api.onchange('picking_type_id', 'partner_id')
    def onchange_picking_type(self):
        res = super(StockPicking, self).onchange_picking_type()
        if self.picking_type_id:
            self.use_documents = self.picking_type_id.code not in ["incoming"]
        return res

    @api.onchange('company_id')
    def _refreshData(self):
        if self.move_lines:
            for m in self.move_lines:
                m.company_id = self.company_id.id

    @api.onchange('vehicle')
    def _setChofer(self):
        self.chofer = self.vehicle.driver_id
        self.patente = self.vehicle.license_plate


class Referencias(models.Model):
    _name = 'stock.picking.referencias'
    _description = 'Referencias en guia de despacho' 

    origen = fields.Char(
            string="Origin",
        )
    sii_referencia_TpoDocRef = fields.Many2one(
            'sii.document_class',
            string="SII Reference Document Type",
        )
    date = fields.Date(
            string="Fecha de la referencia",
        )
    stock_picking_id = fields.Many2one(
            'stock.picking',
            ondelete='cascade',
            index=True,
            copy=False,
            string="Documento",
        )


class StockMove(models.Model):
    _inherit = 'stock.move'
    
    @api.multi
    def _get_discount_total(self):
        product_qty = self.quantity_done
        if product_qty <= 0:
            product_qty = self.product_uom_qty
        return (self.discount_value * product_qty) or (self.precio_unitario * product_qty * self.discount * 0.01)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'picking_id' in vals:
                picking = self.env['stock.picking'].browse(vals['picking_id'])
                if picking and picking.company_id:
                    vals.update({'company_id': picking.company_id.id})
        return super(StockMove, self).create(vals_list)

    def _set_price_from(self):
        if self.picking_id.reference:
            for ref in self.picking_id.reference:
                if ref.sii_referencia_TpoDocRef.sii_code in [33]:
                    il = self.env['account.invoice'].search(
                            [
                                    ('sii_document_number', '=', ref.origen),
                                    ('sii_document_class_id.sii_code', '=', ref.sii_referencia_TpoDocRef.sii_code),
                                    ('product_id', '=', self.product_id.id),
                            ]
                        )
                    if il:
                        self.precio_unitario = il.price_unit
                        self.subtotal = il.subtotal
                        self.discount = il.discount
                        self.move_line_tax_ids = il.invoice_line_tax_ids

    @api.onchange('name')
    def _sale_prices(self):
        for rec in self:
            if rec.precio_unitario <= 0:
                rec._set_price_from()
            if rec.precio_unitario <= 0:
                rec.precio_unitario = rec.product_id.lst_price
                rec.move_line_tax_ids = rec.product_id.taxes_id # @TODO mejorar asignación
            if not rec.name:
                rec.name = rec.product_id.name

    @api.depends('name', 'product_id', 'move_line_tax_ids', 'product_uom_qty', 'precio_unitario', 'quantity_done', 'discount', 'discount_value')
    def _compute_amount(self):
        for rec in self:
            logging.info("JESUS CORRECCIOM***********************************")
            qty = rec.quantity_done
            if qty <= 0:
                qty = rec.product_uom_qty
            discount_total = float_round(rec._get_discount_total(), precision_digits=rec.currency_id.decimal_places)
            subtotal = float_round(qty * rec.precio_unitario, precision_digits=rec.currency_id.decimal_places)
            taxes = rec.move_line_tax_ids.compute_all(subtotal - discount_total, rec.currency_id, 1, product=rec.product_id, partner=rec.picking_id.partner_id, discount=rec.discount, uom_id=rec.product_uom)
            rec.price_untaxed = taxes['total_excluded']
            if rec.discount : 
                t = (rec.precio_unitario * rec.product_uom_qty) -   ((rec.precio_unitario * rec.product_uom_qty) * rec.discount)/100
                rec.subtotal = t
            else:
                rec.subtotal = (rec.precio_unitario * rec.product_uom_qty) 
            
    @api.onchange('discount')
    def _onchange_discount(self):
        self.discount_value = 0

    name = fields.Char(
            string="Nombre",
        )
    subtotal = fields.Monetary(
            compute='_compute_amount',
            string='Subtotal',
            store=True,
        )
    precio_unitario = fields.Float(
            string='Precio Unitario',
            digits=dp.get_precision('Product Price'),
        )
    price_untaxed = fields.Monetary(
            string='Price Untaxed',
            compute='_compute_amount',
        )
    move_line_tax_ids = fields.Many2many(
            'account.tax',
            'move_line_tax_ids',
            'move_line_id',
            'tax_id',
            string='Taxes',
            domain=[('type_tax_use', '!=', 'none'), '|', ('active', '=', False), ('active', '=', True)],
        )
    discount = fields.Float(
            digits=dp.get_precision('Discount'),
            string='Discount (%)',
        )
    discount_value = fields.Float(u'Descuento Monto', digits=dp.get_precision('Account'))
    currency_id = fields.Many2one(
            'res.currency',
            string='Currency',
            required=True,
            states={'draft': [('readonly', False)]},
            default=lambda self: self.env.user.company_id.currency_id.id,
            track_visibility='always',
        )
    
    def _get_new_picking_values(self):
        vals = super(StockMove, self)._get_new_picking_values()
        if self.sale_line_id.order_id.carrier_id:
            # si el pedido de venta tiene metodo de envio
            # pasar el Tipo de despacho como Despacho externo
            vals['transport_type'] = '3'
        return vals
