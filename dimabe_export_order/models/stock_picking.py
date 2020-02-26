from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    delivery_date = fields.Datetime('Fecha de entrega')

    shipping_number = fields.Integer('Número Embarque')

    shipping_id = fields.Many2one(
        'custom.shipment',
        'Embarque'
    )

    required_loading_date = fields.Date(
        related='shipping_id.required_loading_date')

    variety = fields.Many2many(related="product_id.attribute_value_ids")

    country = fields.Char(related='partner_id.country_id.name')

    quantity_done = fields.Float(
        related='move_ids_without_package.product_uom_qty')

    product = fields.Many2one(related="move_ids_without_package.product_id")

    contract_correlative = fields.Integer('corr')

    contract_correlative_view = fields.Char(
        'N° Orden',
        compute='_get_correlative_text'
    )

    consignee_id = fields.Many2one(
        'res.partner',
        'Consignatario',
        domain=[('customer', '=', True)]
    )

    notify_ids = fields.Many2many(
        'res.partner',
        domain=[('customer', '=', True)]
    )

    agent_id = fields.Many2one(
        'res.partner',
        'Agente',
        domain=[('is_agent', '=', True), ('commission', '>', 0)]
    )

    total_commission = fields.Float(
        'Valor Comisión',
        compute='_compute_total_commission'
    )

    charging_mode = fields.Selection(
        [
            ('piso', 'A Piso'),
            ('slip_sheet', 'Slip Sheet'),
            ('palet', 'Paletizado')
        ],
        'Modo de Carga'
    )

    booking_number = fields.Char('N° Booking')

    bl_number = fields.Char('N° BL')

    client_label = fields.Boolean('Etiqueta Cliente', default=False)

    client_label_file = fields.Binary(string='Archivo Etiqueta Cliente')

    container_number = fields.Char('N° Contenedor')

    freight_value = fields.Float('Valor Flete')

    safe_value = fields.Float('Valor Seguro')

    total_value = fields.Float(
        'Valor Total',
        compute='_compute_total_value',
        store=True
    )

    value_per_kilogram = fields.Float(
        'Valor por kilo',
        compute='_compute_value_per_kilogram',
        store=True
    )

    remarks = fields.Text('Comentarios')

    container_type = fields.Many2one(
        'custom.container.type',
        'Tipo de contenedor'
    )

    net_weight_dispatch = fields.Integer(string="Kilos Netos")

    gross_weight_dispatch = fields.Integer(string="Kilos Brutos")

    tare_container_weight_dispatch = fields.Integer(string="Tara Contenedor")

    container_weight = fields.Integer(string="Peso Contenedor")

    vgm_weight_dispatch = fields.Integer(string="Peso VGM", compute="get_vgm_weight", store=True)

    note_dispatched = fields.Many2one('custom.note')

    sell_truck = fields.Char(string="Sello de Camión")

    guide_number = fields.Char(string="Numero de Guia")

    sell_sag = fields.Char(string="Sello SAG")

    gps_lock = fields.Char(string="Candado GPS")

    gps_button = fields.Char(string="Botón GPS")

    dus_number = fields.Integer(string="Numero DUS")

    picture = fields.Many2many("ir.attachment", string="Fotos Camión")

    file = fields.Char(related="picture.datas_fname")

    type_of_transfer_list = fields.Selection(
        [('1', 'Operacion constituye venta'),
         ('2', 'Ventas por efectuar'),
         ('3', 'Consignaciones'),
         ('4', 'Entrega gratuita'),
         ('5', 'Traslado internos'),
         ('6', 'Otros traslados no venta'),
         ('7', 'Guia de devolucion'),
         ('8', 'Traslado para exportación no venta'),
         ('9', 'Venta para exportacion')]
        , string="Tipo de Traslado"
    )

    type_of_transfer = fields.Char(compute="get_type_of_transfer")

    transport = fields.Char(string="Transporte")

    type_of_dispatch = fields.Selection([('exp', 'Exportación'), ('nac', 'Nacional')], string="Tipo de Despacho")

    sell_shipping = fields.Char(string="Sello Naviera")

    is_dispatcher = fields.Integer(compute="get_permision")

    hour_arrival = fields.Float(string="Hora de Llegada")

    hour_departure = fields.Float(string="Hora de Salida")

    @api.multi
    def generate_report(self):

        return self.env.ref('dimabe_export_order.action_dispatch_label_report') \
            .report_action(self.picture)

    @api.onchange('hour_arrival')
    def check_time(self):
        models._logger.error(self.hour_arrival)

    @api.multi
    def get_permision(self):
        for i in self.env.user.groups_id:
            if i.name == "Despachos":
                self.is_dispatcher = 1

    @api.multi
    def get_type_of_transfer(self):
        models._logger.error(self.is_dispatcher)
        self.type_of_transfer = \
            dict(self._fields['type_of_transfer_list'].selection).get(self.type_of_transfer_list)
        return self.type_of_transfer

    @api.one
    @api.depends('tare_container_weight_dispatch', 'container_weight')
    def get_vgm_weight(self):

        self.vgm_weight_dispatch = \
            self.tare_container_weight_dispatch + self.container_weight

    @api.model
    @api.depends('freight_value', 'safe_value')
    def _compute_total_value(self):
        print('')
        # cambiar amount_total
        # data = self.amount_total - self.freight_value - self.safe_value
        # self.total_value = data

    @api.model
    @api.depends('total_value')
    def _compute_value_per_kilogram(self):
        print('')
        # qty_total = 0
        # for line in self.order_line:
        # qty_total = qty_total + line.product_uom_qty
        # if qty_total > 0:
        # self.value_per_kilogram = self.total_value / qty_total

    @api.model
    @api.depends('agent_id')
    def _compute_total_commission(self):
        print('')
        # cambiar amount_total
        # self.total_commission = (self.agent_id.commission / 100) * self.amount_total

    @api.model
    # @api.depends('contract_id')
    def _get_correlative_text(self):
        print('')
        # if self.contract_id:
        # if self.contract_correlative == 0:
        # existing = self.contract_id.sale_order_ids.search([('name', '=', self.name)])
        # if existing:
        # self.contract_correlative = existing.contract_correlative
        # if self.contract_correlative == 0:
        # self.contract_correlative = len(self.contract_id.sale_order_ids)
        # else:
        # self.contract_correlative = 0
        # if self.contract_id.name and self.contract_correlative and self.contract_id.container_number:
        # self.contract_correlative_view = '{}-{}/{}'.format(
        # self.contract_id.name,
        # self.contract_correlative,
        # self.contract_id.container_number
        # )
        # else:
        # self.contract_correlative_view = ''
