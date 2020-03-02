from odoo import fields, models, api


class UnpelledDried(models.Model):
    _name = 'unpelled.dried'
    _description = 'clase que para producción de secado y despelonado'

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('progress', 'En Proceso'),
        ('done', 'Terminado'),
        ('cancel', 'Cancelado')
    ],
        'Estado'
    )

    name = fields.Char(
        'Proceso',
        compute='_compute_name'
    )

    producer_id = fields.Many2one(
        'res.partner',
        'Productor',
        domain=[('supplier', '=', True)]
    )

    product_in_id = fields.Many2one(
        'product.product',
        'Producto a ingresar',
        domain=[('categ_id.name', 'ilike', 'verde')]
    )

    in_lot_ids = fields.Many2many(
        'stock.production.lot',
        string='Lotes de Entrada'
    )

    out_lot_id = fields.Many2one(
        'stock.production.lot',
        'Lote Producción'
    )

    out_serial_ids = fields.One2many(
        'stock.production.lot.serial',
        compute='_compute_out_serial_ids',
        inverse='_inverse_out_serial_ids'
    )

    out_product_id = fields.Many2one(
        'product.product',
        'Producto de Salida',
        required=True
    )

    oven_use_ids = fields.One2many(
        'oven.use',
        'unpelled_dried_id',
        'Hornos'
    )

    @api.onchange('producer_id')
    def onchange_producer_id(self):
        if self.producer_id not in self.in_lot_ids.mapped('producer_id'):
            self.in_lot_ids = [(5,)]

    @api.multi
    def _compute_out_serial_ids(self):
        for item in self:
            item.out_serial_ids = item.out_lot_id.stock_production_lot_serial_ids

    @api.multi
    def _inverse_out_serial_ids(self):
        for item in self:
            item.out_lot_id.stock_production_lot_serial_ids = item.out_serial_ids

    @api.multi
    def _compute_name(self):
        for item in self:
            item.name = item.out_lot_id.name

    @api.model
    def create(self, values_list):
        res = super(UnpelledDried, self).create(values_list)

        res.state = 'draft'

        name = self.env['ir.sequence'].next_by_code('unpelled.dried')

        out_lot = self.env['stock.production.lot'].create({
            'name': name,
            'product_id': res.out_product_id.id,
            'is_prd_lot': True  # probar si funciona bien, de lo contrario dejar en False
        })

        res.out_lot_id = out_lot.id

        return res

    @api.multi
    def cancel_unpelled_dried(self):
        for item in self:
            item.state = 'cancel'
            item.oven_use_ids.mapped('dried_oven_id').set_is_in_use(False)

    @api.multi
    def finish_unpelled_dried(self):
        for item in self:
            item.state = 'done'
            item.oven_use_ids.mapped('dried_ove_id').set_is_in_use(False)
