from odoo import fields, models, api
from odoo.addons import decimal_precision as dp
from datetime import datetime
import inspect


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    positioning_state = fields.Selection([
        ('pending', 'Pendiente'),
        ('done', 'Listo')
    ],
        'Estado movimiento de bodega a producción',
        default='pending'
    )

    client_id = fields.Many2one(
        'res.partner',
        related='stock_picking_id.partner_id',
        string='Cliente',
        readonly=True
    )

    destiny_country_id = fields.Many2one(
        'res.country',
        related='stock_picking_id.arrival_port.country_id',
        string='País'
    )

    charging_mode = fields.Selection(
        related='stock_picking_id.charging_mode',
        string='Modo de Carga'
    )

    client_label = fields.Boolean(
        'Etiqueta Cliente',
        related='stock_picking_id.client_label'
    )

    unevenness_percent = fields.Float(
        '% Descalibre',
        digits=dp.get_precision('Product Unit of Measure')
    )

    etd = fields.Date(
        'Fecha Despacho',
        related='stock_picking_id.etd'
    )

    observation = fields.Text('Observación')

    label_durability_id = fields.Many2one(
        'label.durability',
        'Durabilidad Etiqueta'
    )

    pt_balance = fields.Float(
        'Saldo Bodega PT',
        digits=dp.get_precision('Product Unit of Measure'),
        compute='_compute_pt_balance'
    )

    stock_picking_id = fields.Many2one('stock.picking', 'Despacho')

    sale_order_id = fields.Many2one(
        'sale.order',
        related='stock_picking_id.sale_id'
    )

    stock_lots = fields.Many2one("stock.production.lot")

    client_search_id = fields.Many2one(
        'res.partner',
        'Buscar Cliente',
        nullable=True
    )

    show_finished_move_line_ids = fields.One2many(
        'stock.move.line',
        compute='_compute_show_finished_move_line_ids'
    )

    consumed_material_ids = fields.One2many(
        'stock.production.lot.serial',
        related='workorder_ids.potential_serial_planned_ids'
    )

    required_date_moving_to_production = fields.Datetime(
        'Fecha Requerida de Movimiento a Producción',
        default=datetime.utcnow()
    )

    product_search_id = fields.Many2one(
        'product.product',
        'Buscar Producto',
        nullable=True,
    )

    product_lot = fields.Many2one(
        'product.product',
        related="stock_lots.product_id"
    )

    requested_qty = fields.Float(
        'Cantidad Solicitada',
        digits=dp.get_precision('Product Unit of Measure')
    )

    serial_lot_ids = fields.One2many(
        'stock.production.lot.serial',
        related="stock_lots.stock_production_lot_serial_ids"
    )

    potential_lot_ids = fields.One2many(
        'potential.lot',
        'mrp_production_id',
        'Posibles Lotes'
    )

    materials = fields.Many2many('product.product', compute='get_product_bom')

    manufactureable = fields.Many2many('product.product', compute='get_product_route')

    @api.multi
    def _compute_pt_balance(self):
        for item in self:
            item.pt_balance = sum(item.stock_picking_id.packing_list_ids.filtered(
                lambda a: a.production_id != item
            ).mapped('display_weight'))

    @api.model
    def get_product_route(self):
        list = []
        for item in self:
            products = item.env['product.product'].search([])
            for p in products:
                if "Fabricar" in p.route_ids.mapped('name'):
                    list.append(p.id)
            item.manufactureable = item.env['product.product'].search([('id', 'in', list)])

    @api.multi
    def get_product_bom(self):
        for item in self:
            item.update({
                'materials': item.bom_id.bom_line_ids.mapped('product_id')
            })

    @api.multi
    def _compute_show_finished_move_line_ids(self):
        for item in self:
            for move_line in item.finished_move_line_ids:
                existing_move = item.show_finished_move_line_ids.filtered(
                    lambda a: a.lot_id == move_line.lot_id
                )
                if not existing_move:
                    move_line.write({
                        'tmp_qty_done': move_line.qty_done
                    })
                    item.show_finished_move_line_ids += move_line
                else:
                    existing_move.write({
                        'tmp_qty_done': existing_move.tmp_qty_done + move_line.qty_done
                    })

    @api.model
    def get_potential_lot_ids(self):
        domain = [
            ('balance', '>', 0),
            ('product_id.id', 'in', list(self.move_raw_ids.filtered(
                lambda a: not a.product_id.categ_id.reserve_ignore
            ).mapped('product_id.id'))),
        ]
        if self.product_search_id:
            domain += [('product_id.id', '=', self.product_search_id.id)]

        if self.client_search_id:
            client_lot_ids = self.env['quality.analysis'].search([
                ('potential_client_id', '=', self.client_search_id.id),
                ('potential_workcenter_id.id', 'in', list(self.routing_id.operation_ids.mapped('workcenter_id.id')))
            ]).mapped('stock_production_lot_ids.name')

            domain += [('name', 'in', list(client_lot_ids) if client_lot_ids else [])]

        res = self.env['stock.production.lot'].search(domain)

        return [{
            'stock_production_lot_id': lot.id,
            'mrp_production_id': self.id
        } for lot in res]

    @api.multi
    def set_stock_move(self):
        product = self.env['stock.move'].create({'product_id': self.product_id})
        product_qty = self.env['stock.move'].create({'product_qty': self.product_qty})
        self.env.cr.commit()

    @api.multi
    def calculate_done(self):
        for item in self:
            lot = item.finished_move_line_ids.mapped('lot_id')
            for line_id in item.finished_move_line_ids:
                line_id.qty_done = line_id.lot_id.total_serial
            for move in item.move_raw_ids.filtered(
                    lambda a: a.product_id not in item.consumed_material_ids.mapped(
                        'product_id') and a.needs_lots is False
            ):
                move.quantity_done = sum(lot.mapped('count_serial')) * sum(item.bom_id.bom_line_ids.filtered(
                    lambda a: a.product_id == move.product_id
                ).mapped('product_qty'))

    @api.multi
    def button_mark_done(self):
        self.calculate_done()
        serial = self.env['stock.production.lot.serial'].search([('reserved_to_production_id.id', '=', self.id)])
        lots = []
        for move in self.move_raw_ids:
            for line in move.active_move_line_ids:
                if line.product_uom_qty != 0:
                    line.sudo().unlink()
                if line.lot_id not in serial.mapped('stock_production_lot_id') or line.lot_id in lots:
                    line.sudo().unlink()
                else:
                    lots.append(line.lot_id)
        res = super(MrpProduction, self).button_mark_done()
        return res

    @api.model
    def create(self, values_list):
        res = super(MrpProduction, self).create(values_list)
        res.stock_picking_id.update({
            'has_mrp_production': True
        })
        return res


    def fix_reserved(self,move):
        query = 'DELETE FROM stock_move_line where move_id = {}'.format(move.id)
        cr = self._cr
        cr.execute(query)
