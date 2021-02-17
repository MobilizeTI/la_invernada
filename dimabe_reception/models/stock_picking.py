from odoo import models, api, fields
from odoo.addons import decimal_precision as dp
from datetime import datetime, date
import requests
import json


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

    is_pt_dispatch = fields.Boolean('Es PT Despacho', compute='_compute_is_pt_dispatch')

    reception_alert = fields.Many2one('reception.alert.config')

    harvest = fields.Char(
        'Cosecha',
        default=datetime.now().year
    )

    @api.multi
    def gross_weight_button(self):
        data = self._get_data_from_weigh()
        self.write({
            'gross_weight': float(data)
        })

    @api.multi
    def button_weight_tare(self):
        data = self._get_data_from_weigh()
        if not self.gross_weight:
            raise models.ValidationError('Debe ingresar el peso bruto')
        self.write({
            'tare_weight': float(data)
        })

    @api.one
    @api.depends('tare_weight', 'gross_weight', 'move_ids_without_package', 'quality_weight')
    def _compute_net_weight(self):
        if self.picking_type_code == 'incoming':
            self.net_weight = self.gross_weight - self.tare_weight + self.quality_weight
            if self.is_mp_reception or self.is_pt_reception or self.is_satelite_reception:
                if self.canning_weight:
                    self.net_weight = self.net_weight - self.canning_weight

    @api.one
    @api.depends('move_ids_without_package')
    def _compute_weight_guide(self):
        if self.picking_type_code == 'incoming':
            if self.is_mp_reception or self.is_pt_reception or self.is_satelite_reception:
                m_move = self.get_mp_move()
                if not m_move:
                    m_move = self.get_pt_move()
                if m_move:
                    self.weight_guide = m_move[0].product_uom_qty

    @api.one
    @api.depends('move_ids_without_package')
    def _compute_canning_weight(self):
        if self.picking_type_code == 'incoming':
            canning = self.get_canning_move()
            if len(canning) == 1 and canning.product_id.weight:
                self.canning_weight = canning.product_uom_qty * canning.product_id.weight

    @api.model
    @api.onchange('gross_weight')
    def on_change_gross_weight(self):
        if self.picking_type_code == 'incoming':
            message = ''
            if self.gross_weight < self.weight_guide:
                message += 'Los kilos brutos deben ser mayor a los kilos de la guía'
                self.gross_weight = 0
            if message:
                raise models.ValidationError(message)

    @api.one
    @api.depends('tare_weight', 'gross_weight', 'move_ids_without_package')
    def _compute_production_net_weight(self):
        if self.picking_type_code == 'incoming':
            self.production_net_weight = self.gross_weight - self.tare_weight + self.quality_weight
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
    def _compute_is_pt_dispatch(self):
        self.is_pt_reception = 'producto terminado' in str.lower(self.picking_type_id.warehouse_id.name) and \
                               'ordenes de entrega' in str.lower(self.picking_type_id.name)

    @api.one
    @api.depends('picking_type_id')
    def _compute_is_satelite_reception(self):
        self.is_satelite_reception = 'packing' in str.lower(self.picking_type_id.warehouse_id.name) and \
                                     'recepciones' in str.lower(self.picking_type_id.name)

    @api.one
    @api.depends('net_weight', 'tare_weight', 'gross_weight', 'move_ids_without_package')
    def _compute_avg_unitary_weight(self):
        if self.picking_type_code == 'incoming':
            if self.net_weight:
                canning = self.get_canning_move()
                if len(canning) == 1:
                    divisor = canning.product_uom_qty
                    if divisor == 0:
                        divisor = 1

                    self.avg_unitary_weight = self.net_weight / divisor

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

    def _get_data_from_weigh(self):
        try:
            res = requests.request('POST', 'http://201.217.253.174:8899/romana/index.py')
            json_data = json.loads(res.text.strip())
            return json_data['value']
        except Exception as e:
            if 'HTTPConnectionPool' in str(e):
                raise models.ValidationError(
                    "Por favor comprobar si el equipo de romana se encuentre encendido o con conexion a internet")
            else:
                raise models.ValidationError(str(e))

    @api.multi
    def action_confirm(self):
        if self.picking_type_code == 'incoming':
            models._logger.error(f'Canning Weight {self.canning_weight}')
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
                            'standard_weight': stock_picking.net_weight,
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
                                        models._logger.error(i == int(total_qty))
                                        models._logger.error(
                                            stock_picking.net_weight - (int(total_qty) * default_value))
                                        if i == int(total_qty):

                                            diff = stock_picking.net_weight - (
                                                    int(total_qty) * default_value)

                                            tmp = '00{}'.format(i + 1)
                                            self.env['stock.production.lot.serial'].create({
                                                'calculated_weight': default_value + diff,
                                                'stock_production_lot_id': stock_move_line.lot_id.id,
                                                'serial_number': '{}{}'.format(stock_move_line.lot_name, tmp[-3:])
                                            })
                                        else:
                                            tmp = '00{}'.format(i + 1)
                                            self.env['stock.production.lot.serial'].create({
                                                'calculated_weight': default_value,
                                                'stock_production_lot_id': stock_move_line.lot_id.id,
                                                'serial_number': '{}{}'.format(stock_move_line.lot_name, tmp[-3:])
                                            })
                                    stock_move_line.lot_id.write({
                                        'available_kg': sum(
                                            stock_move_line.lot_id.stock_production_lot_serial_ids.mapped(
                                                'display_weight'))
                                    })
                                    m_move.has_serial_generated = True
                return res
        else:
            return super(StockPicking, self).action_confirm()

    @api.multi
    def button_validate(self):
        if self.picking_type_code == 'incoming':
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
                            'verde' not in str.lower(stock_picking.picking_type_id.warehouse_id.name):
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
                m_move.quantity_done = self.net_weight
                m_move.product_uom_qty = self.weight_guide
                if m_move.has_serial_generated and self.avg_unitary_weight:
                    self.env['stock.production.lot.serial'].search([('stock_production_lot_id', '=', self.name)]).write(
                        {
                            'real_weight': self.avg_unitary_weight
                        })
                    canning = self.get_canning_move()
                    if len(canning) == 1:
                        diff = self.net_weight - (canning.product_uom_qty * self.avg_unitary_weight)
                        self.env['stock.production.lot.serial'].search([('stock_production_lot_id', '=', self.name)])[
                            -1].write({
                            'real_weight': self.avg_unitary_weight + diff
                        })

            return res
        # Se usaran datos de modulo de dimabe_manufacturing
        if self.picking_type_code == 'outgoing':
            if 'producto terminado' in str.lower(self.picking_type_id.warehouse_id.name) and \
                    'ordenes de entrega' in str.lower(self.picking_type_id.name):
                self.packing_list_ids.write({
                    'consumed': True
                })
                if self.dispatch_line_ids:
                    for dispatch in self.dispatch_line_ids:
                        self.clean_reserved(dispatch.dispatch_id)
                        if not dispatch.dispatch_id.move_line_ids_without_package.filtered(
                                lambda a: a.product_id.id == dispatch.product_id.id):
                            self.env['stock.move.line'].create({
                                'picking_id': dispatch.dispatch_id.id,
                                'product_id': dispatch.product_id.id,
                                'product_uom_id': dispatch.product_id.uom_id.id,
                                'lot_id': self.move_line_ids_without_package.filtered(lambda
                                                                                          a: a.product_id.id == dispatch.product_id.id and a.sale_order_id.id == dispatch.sale_id.id).lot_id.id,
                                'product_uom_qty': dispatch.real_dispatch_qty,
                                'location_id': dispatch.dispatch_id.location_id.id,
                                'location_dest_id': dispatch.dispatch_id.partner_id.property_stock_customer.id,
                                'move_id': dispatch.dispatch_id.move_ids_without_package.filtered(
                                    lambda m: m.product_id.id == dispatch.product_id.id).id,
                                'date': date.today()
                            })
                        else:
                            dispatch.dispatch_id.move_line_ids_without_package.filtered(lambda
                                                                                            m: m.product_id.id == dispatch.product_id and self.move_line_ids_without_package.filtered(
                                lambda
                                    a: a.product_id.id == dispatch.product_id.id and a.sale_order_id.id == dispatch.sale_id.id).lot_id.id).write({
                                'product_uom_qty':dispatch.real_dispatch_qty
                            })
                for stock in self.move_line_ids_without_package.filtered(lambda a: a.lot_id).mapped('lot_id'):
                    quant = self.env['stock.quant'].search(
                        [('lot_id', '=', stock.id), ('location_id.usage', '=', 'internal')])
                    quant.write({
                        'reserved_quantity': sum(stock.stock_production_lot_serial_ids.filtered(lambda
                                                                                                    x: x.reserved_to_stock_picking_id and x.reserved_to_stock_picking_id.state != 'done' and not x.consumed).mapped(
                            'display_weight')),
                        'quantity': sum(stock.stock_production_lot_serial_ids.filtered(
                            lambda x: not x.reserved_to_stock_picking_id and not x.consumed).mapped('display_weight'))
                    })

                    quant.write({
                        'reserved_quantity': sum(stock.stock_production_lot_serial_ids.filtered(
                            lambda a: a.reserved_to_stock_picking_id).mapped('display_weight')),
                    })
        return super(StockPicking, self).button_validate()

    def clean_reserved(self, picking):
        picking.move_line_ids_without_package.filtered(lambda a: not a.lot_id).unlink()
        for lot in picking.move_line_ids.mapped('lot_id'):
            if lot not in self.packing_list_lot_ids:
                picking.move_line_ids_without_package.filtered(lambda a: a.lot_id.id == lot.id).unlink()

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
        if self.is_mp_reception:
            if len(self.move_ids_without_package) > len(self.move_ids_without_package.mapped('product_id')):
                raise models.ValidationError('no puede tener el mismo producto en más de una linea')
