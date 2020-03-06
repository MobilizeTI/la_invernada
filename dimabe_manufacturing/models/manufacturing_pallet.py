from odoo import api, models, fields


class ManufacturingPallet(models.Model):
    _name = 'manufacturing.pallet'
    _description = 'clase para paletizaje de series de lote'
    _inherit = ['barcodes.barcode_events_mixin']

    active = fields.Boolean(
        'Activo',
        default=True
    )

    state = fields.Selection([
        ('open', 'Abierto'),
        ('close', 'Cerrado')
    ],
        string='Estado',
        default='open'
    )

    name = fields.Char('Pallet')

    producer_id = fields.Many2one(
        'res.partner',
        'Productor',
        domain=[('supplier', '=', True)],
        states={'close': [('readonly', True)], 'open': [('readonly', False)]}
    )

    product_id = fields.Many2one(
        'product.product',
        compute='_compute_product_id',
        store=True
    )

    add_manual_code = fields.Boolean(
        'Agregar Código Manualmente',
        states={'close': [('invisible', True)], 'open': [('invisible', False)]}
    )

    manual_code = fields.Char(
        'Código Manual',
        states={'close': [('invisible', True)], 'open': [('invisible', False)]}
    )

    sag_code = fields.Char(
        related='producer_id.sag_code'
    )

    lot_serial_ids = fields.One2many(
        'stock.production.lot.serial',
        'pallet_id',
        states={'close': [('readonly', True)], 'open': [('readonly', False)]}
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

    total_content_weight = fields.Float(
        'Peso Total',
        compute='_compute_total_weight_content'
    )

    @api.model
    def create(self, values_list):
        res = super(ManufacturingPallet, self).create(values_list)

        res.name = self.env['ir.sequence'].next_by_code('manufacturing.pallet')

        return res

    @api.multi
    def _compute_total_weight_content(self):
        for item in self:
            item.total_content_weight = sum(item.lot_serial_ids.mapped('display_weight'))

    @api.multi
    @api.depends('lot_serial_ids')
    def _compute_product_id(self):
        for item in self:
            counter = 0
            for serial_id in item.lot_serial_ids:
                tmp = len(item.lot_serial_ids.filtered(
                    lambda a: a.stock_product_id == serial_id.stock_product_id
                ))
                if counter < tmp:
                    item.product_id = serial_id.stock_product_id
                    counter = tmp

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

    @api.multi
    def add_code(self):
        for item in self:
            item.on_barcode_scanned(item.manual_code)

    @api.multi
    def close_pallet(self):
        for item in self:
            item.set_state('close')

    @api.multi
    def open_pallet(self):
        for item in self:
            item.set_state('open')

    @api.multi
    def print_pallet_label(self):
        for item in self:
            return self.env.ref('dimabe_manufacturing.action_manufacturing_pallet_label_report') \
                .report_action(item)

    @api.model
    def set_state(self, state):
        self.state = state

    @api.multi
    def get_full_url(self):
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return base_url

    @api.multi
    def show_pallet(self):
        for item in self:
            return {
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_model': 'manufacturing.pallet',
                'res_id': item.id,
                'view_mode': 'form',
                'flags': {'initial_mode': 'edit'}
            }

    @api.returns('self')
    def on_barcode_scanned(self, barcode):

        serial_id = self.env['stock.production.lot.serial'].search([
            ('serial_number', '=', barcode),
            ('consumed', '=', False)
        ])

        if not serial_id:
            raise models.ValidationError('no se encontró ningún registro asociado a este código')

        if serial_id.pallet_id.state == 'close':
            raise models.ValidationError('Este código se encuentra en un pallet cerrado ({})'
                                         'debe abrir el pallet para poder cambiar la caja de pallet'.format(
                serial_id.pallet_id.name
            ))

        lot_serial_ids = list(self.lot_serial_ids.mapped('id'))

        if serial_id.id not in lot_serial_ids:
            lot_serial_ids.append(serial_id.id)

        self.update({
            'lot_serial_ids': [(6, 0, lot_serial_ids)]
        })

        # serial_id.write({
        #     'pallet_id': self.id
        # })

        return self

        raise models.ValidationError([(6, 0, lot_serial_ids)])

