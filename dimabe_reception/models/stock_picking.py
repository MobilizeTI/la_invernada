from odoo import models, api, fields
from datetime import datetime


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _order = 'date desc'

    guide_number = fields.Integer('Número de Guía')

    weight_guide = fields.Integer(
        'Kilos Guía',
        compute='_compute_weight_guide',
        store=True
    )

    gross_weight = fields.Integer('Kilos Brutos')

    tare_weight = fields.Integer('Peso Tara')

    net_weight = fields.Integer(
        'Kilos Netos',
        compute='_compute_net_weight',
        store=True
    )

    canning_weight = fields.Float(
        'Peso Envases',
        compute='_compute_canning_weight',
        store=True
    )

    production_net_weight = fields.Float(
        'Kilos Netos Producción',
        compute='_compute_production_net_weight',
        store=True
    )

    reception_type_selection = fields.Selection([
        ('ins', 'Insumos'),
        ('mp', 'Materia Prima')
    ],
        default='ins',
        string='Tipo de recepción'
    )

    is_mp_reception = fields.Boolean(
        'Recepción de MP',
        compute='_compute_is_mp_reception',
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
        compute='_compute_avg_unitary_weight'
    )

    quality_weight = fields.Float('Kilos Calidad')

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
        if self.is_mp_reception:
            if self.canning_weight:
                self.net_weight = self.net_weight - self.canning_weight

    @api.one
    @api.depends('move_ids_without_package')
    def _compute_weight_guide(self):
        if self.is_mp_reception:
            if self.get_mp_move():
                self.weight_guide = self.get_mp_move().product_uom_qty

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
        if self.is_mp_reception:
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
    @api.depends('reception_type_selection', 'picking_type_id')
    def _compute_is_mp_reception(self):

        self.is_mp_reception = self.reception_type_selection == 'mp' or \
                               self.picking_type_id.warehouse_id.name and \
                               'Materia Prima' in self.picking_type_id.warehouse_id.name and \
                               self.picking_type_id.name and 'Recepciones' in self.picking_type_id.name

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
    def get_canning_move(self):
        return self.move_ids_without_package.filtered(lambda x: x.product_id.categ_id.is_canning is True)

    def _get_hours(self, init_date, finish_date):
        diff = str((finish_date - init_date))
        return diff.split('.')[0]

    @api.multi
    def action_confirm(self):
        for stock_picking in self:
            if stock_picking.is_mp_reception:
                stock_picking.validate_mp_reception()
                stock_picking.truck_in_date = fields.datetime.now()
            res = super(StockPicking, self).action_confirm()
            mp_move = stock_picking.get_mp_move()

            if mp_move and mp_move.move_line_ids and mp_move.picking_id.picking_type_code == 'incoming':
                for move_line in mp_move.move_line_ids:
                    lot = self.env['stock.production.lot'].create({
                        'name': stock_picking.name,
                        'product_id': move_line.product_id.id,
                        'standard_weight': stock_picking.net_weight - stock_picking.quality_weight
                    })
                    if lot:
                        move_line.update({
                            'lot_id': lot.id
                        })

                if mp_move.product_id.tracking == 'lot' and not mp_move.has_serial_generated:
                    for stock_move_line in mp_move.move_line_ids:
                        if mp_move.product_id.categ_id.is_mp:
                            total_qty = mp_move.picking_id.get_canning_move().product_uom_qty
                            calculated_weight = stock_move_line.qty_done / total_qty
                            if stock_move_line.lot_id:

                                for i in range(int(total_qty)):
                                    tmp = '00{}'.format(i + 1)
                                    self.env['stock.production.lot.serial'].create({
                                        'calculated_weight': calculated_weight - stock_picking.quality_weight,
                                        'stock_production_lot_id': stock_move_line.lot_id.id,
                                        'serial_number': '{}{}'.format(stock_move_line.lot_name, tmp[-3:])
                                    })

                                mp_move.has_serial_generated = True
            return res

    @api.multi
    def button_validate(self):
        for stock_picking in self:
            message = ''
            if stock_picking.is_mp_reception:
                if not stock_picking.gross_weight:
                    message = 'Debe agregar kg brutos \n'
                if stock_picking.gross_weight < stock_picking.weight_guide:
                    message += 'Los kilos de la Guía no pueden ser mayores a los Kilos brutos ingresados \n'
                if not stock_picking.tare_weight:
                    message += 'Debe agregar kg tara \n'
                if not stock_picking.quality_weight and \
                        'verde' not in str.lower(stock_picking.picking_type_id.warehouse_id.name):
                    message += 'Los kilos de calidad aún no han sido registrados en el sistema,' \
                               ' no es posible cerrar el ciclo de recepción'
                if message:
                    raise models.ValidationError(message)
        res = super(StockPicking, self).button_validate()
        self.sendKgNotify()
        if self.get_mp_move():
            mp_move = self.get_mp_move()
            mp_move.quantity_done = self.net_weight - self.quality_weight
            mp_move.product_uom_qty = self.weight_guide
            if mp_move.has_serial_generated and self.avg_unitary_weight:
                self.env['stock.production.lot.serial'].search([('stock_production_lot_id', '=', self.name)]).write({
                    'real_weight': self.avg_unitary_weight
                })

        return res

    @api.model
    def validate_mp_reception(self):
        message = ''
        if not self.guide_number:
            message = 'debe agregar número de guía \n'
        if not self.weight_guide:
            message += 'debe agregar kilos guía \n'

        if not self.get_canning_move():
            message += 'debe agregar envases'
        if not self.get_mp_move():
            message += 'debe agregar MP'
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

        if len(res.move_ids_without_package) > len(res.move_ids_without_package.mapped('product_id')):
            raise models.ValidationError('no puede tener el mismo producto en mas de una linea')
        return res
