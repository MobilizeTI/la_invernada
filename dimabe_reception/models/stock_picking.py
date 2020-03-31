from odoo import models, api, fields
from odoo.addons import decimal_precision as dp
from datetime import datetime


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _order = 'date desc'

    guide_number = fields.Integer('Número de Guía')

    weight_guide = fields.Float(
        'Kilos Guía',
        compute='_compute_weight_guide',
        store=True,
        digits=dp.get_precision('Product Unit of Measure')
    )

    gross_weight = fields.Float(
        'Kilos Brutos',
        digits=dp.get_precision('Product Unit of Measure')
    )

    tare_weight = fields.Float(
        'Peso Tara',
        digits=dp.get_precision('Product Unit of Measure')
    )

    net_weight = fields.Float(
        'Kilos Netos',
        compute='_compute_net_weight',
        store=True,
        digits=dp.get_precision('Product Unit of Measure')
    )

    canning_weight = fields.Float(
        'Peso Envases',
        compute='_compute_canning_weight',
        store=True,
        digits=dp.get_precision('Product Unit of Measure')
    )

    production_net_weight = fields.Float(
        'Kilos Netos Producción',
        compute='_compute_production_net_weight',
        store=True,
        digits=dp.get_precision('Product Unit of Measure')
    )

    # reception_type_selection = fields.Selection([
    #     ('ins', 'Insumos'),
    #     ('mp', 'Materia Prima')
    # ],
    #     default='ins',
    #     string='Tipo de recepción'
    # )

    is_mp_reception = fields.Boolean(
        'Recepción de MP',
        compute='_compute_is_mp_reception',
        store=True
    )

    is_pt_reception = fields.Boolean(
        'Recepción de PT',
        compute='_compute_is_pt_reception',
        store=True
    )

    is_satelite_reception = fields.Boolean(
        'Recepción Sételite',
        compute='_compute_is_satelite_reception',
        store=True
    )

    carrier_id = fields.Many2one('custom.carrier', 'Conductor')

    truck_in_date = fields.Datetime(
        'Entrada de Camión',
        readonly=True
    )

    elapsed_time = fields.Char(
        'Horas Camión en planta',
        compute='_compute_elapsed_time'
    )

    avg_unitary_weight = fields.Float(
        'Promedio Peso unitario',
        compute='_compute_avg_unitary_weight',
        digits=dp.get_precision('Product Unit of Measure')
    )

    quality_weight = fields.Float(
        'Kilos Calidad',
        digits=dp.get_precision('Product Unit of Measure')
    )

    carrier_rut = fields.Char(
        'Rut',
        related='carrier_id.rut'
    )

    carrier_cell_phone = fields.Char(
        'Celular',
        related='carrier_id.cell_number'
    )

    carrier_truck_patent = fields.Char(
        'Patente Camión',
        related='truck_id.name'
    )

    carrier_cart_patent = fields.Char(
        'Patente Carro',
        related='cart_id.name'
    )

    truck_id = fields.Many2one(
        'transport',
        'Patente Camión',
        context={'default_is_truck': True},
        domain=[('is_truck', '=', True)]
    )

    cart_id = fields.Many2one(
        'transport',
        'Patente Carro',
        context={'default_is_truck': False},
        domain=[('is_truck', '=', False)]

    )

    hr_alert_notification_count = fields.Integer('Conteo de notificación de retraso de camión')

    kg_diff_alert_notification_count = fields.Integer('Conteo de notificación de diferencia de kg')

    sag_code = fields.Char(
        'CSG',
        related='partner_id.sag_code'
    )

    reception_alert = fields.Many2one('reception.alert.config')

    harvest = fields.Char(
        'Cosecha',
        default=datetime.now().year
    )

    @api.one
    @api.depends('tare_weight', 'gross_weight', 'move_ids_without_package', 'quality_weight')
    def _compute_net_weight(self):
        self.net_weight = self.gross_weight - self.tare_weight + self.quality_weight
        if self.is_mp_reception or self.is_pt_reception or self.is_satelite_reception:
            if self.canning_weight:
                self.net_weight = self.net_weight - self.canning_weight

    @api.one
    @api.depends('move_ids_without_package')
    def _compute_weight_guide(self):
        if self.is_mp_reception or self.is_pt_reception or self.is_satelite_reception:
            m_move = self.get_mp_move()
            if not m_move:
                m_move = self.get_pt_move()
            if m_move:
                self.weight_guide = m_move[0].product_uom_qty

    @api.one
    @api.depends('move_ids_without_package')
    def _compute_canning_weight(self):
        canning = self.get_canning_move()
        if len(canning) == 1 and canning.product_id.weight:
            self.canning_weight = canning.product_uom_qty * canning.product_id.weight

    @api.model
    @api.onchange('gross_weight')
    def on_change_gross_weight(self):
        message = ''
        if self.gross_weight < self.weight_guide:
            message += 'Los kilos brutos deben ser mayor a los kilos de la guía'
            self.gross_weight = 0
        if message:
            raise models.ValidationError(message)

    @api.one
    @api.depends('tare_weight', 'gross_weight', 'move_ids_without_package', )
    def _compute_production_net_weight(self):
        self.production_net_weight = self.gross_weight - self.tare_weight
        if self.is_mp_reception or self.is_pt_reception or self.is_satelite_reception:
            if self.canning_weight:
                self.production_net_weight = self.production_net_weight - self.canning_weight

    @api.one
    def _compute_elapsed_time(self):
        if self.truck_in_date:
            if self.date_done:
                self.elapsed_time = self._get_hours(self.truck_in_date, self.date_done)
            else:

                self.elapsed_time = self._get_hours(self.truck_in_date, datetime.now())
        else:
            self.elapsed_time = '00:00:00'

    @api.one
    @api.depends('picking_type_id')  # 'reception_type_selection',
    def _compute_is_mp_reception(self):
        # self.reception_type_selection == 'mp' or \
        self.is_mp_reception = self.picking_type_id.warehouse_id.name and \
                               'materia prima' in str.lower(self.picking_type_id.warehouse_id.name) and \
                               self.picking_type_id.name and 'recepciones' in str.lower(self.picking_type_id.name)

    @api.one
    @api.depends('picking_type_id')
    def _compute_is_pt_reception(self):
        self.is_pt_reception = 'producto terminado' in str.lower(self.picking_type_id.warehouse_id.name) and \
                               'recepciones' in str.lower(self.picking_type_id.name)

    @api.one
    @api.depends('picking_type_id')
    def _compute_is_satelite_reception(self):
        self.is_satelite_reception = 'packing' in str.lower(self.picking_type_id.warehouse_id.name) and \
                                     'recepciones' in str.lower(self.picking_type_id.name)

    @api.one
    @api.depends('production_net_weight', 'tare_weight', 'gross_weight', 'move_ids_without_package')
    def _compute_avg_unitary_weight(self):
        if self.production_net_weight:
            canning = self.get_canning_move()
            if len(canning) == 1:
                divisor = canning.product_uom_qty
                if divisor == 0:
                    divisor = 1
                self.avg_unitary_weight = self.production_net_weight / divisor

    @api.model
    def get_mp_move(self):
        return self.move_ids_without_package.filtered(lambda x: x.product_id.categ_id.is_mp is True)

    @api.model
    def get_pt_move(self):
        return self.move_ids_without_package.filtered(lambda a: a.product_id.categ_id.is_pt)

    @api.model
    def get_canning_move(self):
        return self.move_ids_without_package.filtered(lambda x: x.product_id.categ_id.is_canning is True)

    def _get_hours(self, init_date, finish_date):
        diff = str((finish_date - init_date))
        return diff.split('.')[0]

    @api.multi
    def action_confirm(self):
        for stock_picking in self:
            if stock_picking.is_mp_reception or stock_picking.is_pt_reception or stock_picking.is_satelite_reception:
                stock_picking.validate_mp_reception()
                stock_picking.truck_in_date = fields.datetime.now()
            res = super(StockPicking, self).action_confirm()
            m_move = stock_picking.get_mp_move()
            if not m_move:
                m_move = stock_picking.get_pt_move()

            if m_move and m_move.move_line_ids and m_move.picking_id.picking_type_code == 'incoming':
                for move_line in m_move.move_line_ids:
                    lot = self.env['stock.production.lot'].create({
                        'name': stock_picking.name,
                        'product_id': move_line.product_id.id,
                        'standard_weight': stock_picking.production_net_weight,
                        'producer_id': stock_picking.partner_id.id
                    })
                    if lot:
                        move_line.update({
                            'lot_id': lot.id
                        })

                if m_move.product_id.tracking == 'lot' and not m_move.has_serial_generated:

                    for stock_move_line in m_move.move_line_ids:

                        if m_move.product_id.categ_id.is_mp or m_move.product_id.categ_id.is_pt:
                            total_qty = m_move.picking_id.get_canning_move().product_uom_qty
                            # calculated_weight = stock_move_line.qty_done / total_qty

                            if stock_move_line.lot_id:
                                default_value = stock_picking.avg_unitary_weight or 1
                                for i in range(int(total_qty)):
                                    tmp = '00{}'.format(i + 1)
                                    self.env['stock.production.lot.serial'].create({
                                        'calculated_weight': default_value,
                                        'stock_production_lot_id': stock_move_line.lot_id.id,
                                        'serial_number': '{}{}'.format(stock_move_line.lot_name, tmp[-3:])
                                    })

                                m_move.has_serial_generated = True
            return res

    @api.multi
    def button_validate(self):
        for stock_picking in self:
            message = ''
            if stock_picking.is_mp_reception or stock_picking.is_pt_reception or stock_picking.is_satelite_reception:
                if not stock_picking.gross_weight:
                    message = 'Debe agregar kg brutos \n'
                if stock_picking.gross_weight < stock_picking.weight_guide:
                    message += 'Los kilos de la Guía no pueden ser mayores a los Kilos brutos ingresados \n'
                if not stock_picking.tare_weight:
                    message += 'Debe agregar kg tara \n'
                if not stock_picking.quality_weight and \
                        ('verde' not in str.lower(stock_picking.picking_type_id.warehouse_id.name)
                        and 'packing' not in str.lower(stock_picking.picking_type_id.warehouse_id.name)):
                    message += 'Los kilos de calidad aún no han sido registrados en el sistema,' \
                               ' no es posible cerrar el ciclo de recepción'
                if message:
                    raise models.ValidationError(message)
        res = super(StockPicking, self).button_validate()
        self.sendKgNotify()
        if self.get_mp_move() or self.get_pt_move():
            m_move = self.get_mp_move()
            if not m_move:
                m_move = self.get_pt_move()
            m_move.quantity_done = self.production_net_weight
            m_move.product_uom_qty = self.weight_guide
            if m_move.has_serial_generated and self.avg_unitary_weight:
                self.env['stock.production.lot.serial'].search([('stock_production_lot_id', '=', self.name)]).write({
                    'real_weight': self.avg_unitary_weight
                })

        return res

    @api.model
    def validate_mp_reception(self):
        message = ''
        if not self.guide_number or not self.guide_number > 0:
            message = 'debe agregar número de guía \n'
        if not self.weight_guide:
            message += 'debe agregar kilos guía \n'

        if not self.get_canning_move():
            message += 'debe agregar envases'
        if not self.get_mp_move() and not self.get_pt_move():
            message += 'debe agregar Materia a recepcionar'
        if message:
            raise models.ValidationError(message)

    @api.multi
    def get_full_url(self):
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return base_url

    def sendKgNotify(self):
        if self.kg_diff_alert_notification_count == 0:
            if self.weight_guide > 0 and self.net_weight > 0:
                alert_config = self.env['reception.alert.config'].search([])
                if abs(self.weight_guide - self.net_weight) > alert_config.kg_diff_alert:
                    self.ensure_one()
                    self.reception_alert = alert_config
                    template_id = self.env.ref('dimabe_reception.diff_weight_alert_mail_template')
                    self.message_post_with_template(template_id.id)
                    self.kg_diff_alert_notification_count += self.kg_diff_alert_notification_count

    @api.multi
    def notify_alerts(self):
        alert_config = self.env['reception.alert.config'].search([])
        elapsed_datetime = datetime.strptime(self.elapsed_time, '%H:%M:%S')
        if self.hr_alert_notification_count == 0 and elapsed_datetime.hour >= alert_config.hr_alert:
            self.ensure_one()
            self.reception_alert = alert_config
            template_id = self.env.ref('dimabe_reception.truck_not_out_mail_template')
            self.message_post_with_template(template_id.id)
            self.hr_alert_notification_count += 1

    @api.model
    def create(self, values_list):
        res = super(StockPicking, self).create(values_list)

        res.validate_same_product_lines()

        return res

    @api.multi
    def write(self, vals):
        res = super(StockPicking, self).write(vals)

        for item in self:
            item.validate_same_product_lines()

        return res

    @api.model
    def validate_same_product_lines(self):
        if len(self.move_ids_without_package) > len(self.move_ids_without_package.mapped('product_id')):
            raise models.ValidationError('no puede tener el mismo producto en más de una linea')
