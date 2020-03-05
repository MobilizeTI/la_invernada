from odoo import api, models, fields


class ManufacturingPallet(models.Model):
    _name = 'manufacturing.pallet'
    _description = 'clase para paletizaje de series de lote'
    _inherit = ['barcodes.barcode_events_mixin']

    name = fields.Char('Pallet')

    product_id = fields.Many2one(
        'product.product',
        'Producto',
        required=True
    )

    producer_id = fields.Many2one(
        'res.partner',
        'Productor',
        domain=[('supplier', '=', True)]
    )

    sag_code = fields.Char(
        related='producer_id.sag_code'
    )

    lot_serial_ids = fields.One2many(
        'stock.production.lot.serial',
        'pallet_id',
        domain=[('pallet_id', '=', False)]
    )

    lot_available_serial_ids = fields.One2many(
        'stock.production.lot.serial',
        compute='_compute_lot_available_serial_ids'
    )

    total_content = fields.Integer(
        'Cantidad',
        compute='_compute_total_content',
        store=True
    )

    total_available_content = fields.Integer(
        'Cantidad Disponible',
        compute='_compute_total_available_content',
        store=True
    )

    @api.model
    def create(self, values_list):
        res = super(ManufacturingPallet, self).create(values_list)

        res.name = self.env['ir.sequence'].next_by_code('manufacturing.pallet')

        return res

    @api.multi
    @api.depends('lot_serial_ids')
    def _compute_total_content(self):
        for item in self:
            item.total_content = len(item.lot_serial_ids)

    @api.multi
    def _compute_lot_available_serial_ids(self):
        for item in self:
            item.lot_available_serial_ids = item.lot_serial_ids.filtered(
                lambda a: not a.consumed
            )

    @api.multi
    def _compute_total_available_content(self):
        for item in self:
            item.total_available_content = len(item.lot_available_serial_ids)

    def on_barcode_scanned(self, barcode):

        serial_id = self.env['stock.production.lot.serial'].search([
            ('serial_number', '=', barcode),
            ('pallet_id', '=', False)
        ])

        if not serial_id:
            raise models.ValidationError('no se encontró ningún registro asociado a este código')

        if serial_id.stock_product_id.id != self.product_id.id:
            raise models.ValidationError('el producto del código escaneado ({}) '
                                         'no corresponde al del pallet ({})'.format(
                serial_id.stock_product_id.display_name,
                self.product_id.display_name
            ))

        serial_id.update({
            'pallet_id': self.id
        })
