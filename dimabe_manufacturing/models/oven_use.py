from odoo import fields, models, api, _
from datetime import datetime
from ..helpers import date_helper


class OvenUse(models.Model):
    _name = 'oven.use'
    _description = 'datos de uso de los hornos'

    ready_to_close = fields.Boolean('Listo para Cerrar')

    name = fields.Char(
        'Horno en uso',
        compute='_compute_name'
    )

    done = fields.Boolean('Listo')

    init_date = fields.Datetime('Inicio de Proceso')

    finish_date = fields.Datetime('Termino de Proceso')

    active_seconds = fields.Integer('Tiempo Transcurrido')

    active_time = fields.Char(
        'Tiempo Transcurrido',
        compute='_compute_active_time',
        store=True
    )

    used_lot_id = fields.Many2one(
        'stock.production.lot',
        'Lote a Secar',
        required=True
    )

    lot_producer_id = fields.Many2one(
        'res.partner',
        related='used_lot_id.producer_id'
    )

    lot_guide_number = fields.Integer(
        'N° Guía',
        related='used_lot_id.reception_guide_number'
    )

    lot_variety = fields.Char(
        'Variedad',
        related='used_lot_id.product_variety'
    )

    lot_picking_type_id = fields.Many2one(
        'stock.picking.type',
        related='used_lot_id.picking_type_id'
    )

    init_active_time = fields.Integer('Inicio de tiempo activo')

    finish_active_time = fields.Integer('Fin de tiempo activo')

    dried_oven_ids = fields.Many2many(
        'dried.oven',
        string='Hornos',
        required=True
    )

    unpelled_dried_id = fields.Many2one('unpelled.dried', 'Proceso de secado')

    history_id = fields.Many2one('dried.unpelled.history', 'Historial')

    out_lot_id = fields.Many2one(
        'stock.production.lot',
        related='history_id.out_lot_id'
    )

    out_lot_serial_count = fields.Integer(
        'Cantidad Envases',
        related='history_id.out_serial_count'
    )

    reception_net_weight = fields.Integer(
        'Kg Entrada',
        related='used_lot_id.reception_net_weight'
    )

    total_out_weight = fields.Float(
        'Kg Salida',
        related='history_id.total_out_weight'
    )

    performance = fields.Float(
        'Rendimiento',
        related='history_id.performance'
    )

    stock_picking_id = fields.Many2one(
        'stock.picking',
        related='used_lot_id.stock_picking_id',
        string='Lote'
    )

    @api.multi
    def _compute_name(self):
        for item in self:
            tmp = ''
            for name in item.dried_oven_ids.mapped('name'):
                tmp += '{} '.format(name)
            item.name = tmp

    @api.multi
    @api.depends('active_seconds')
    def _compute_active_time(self):
        for item in self:
            item.active_time = date_helper.int_to_time(item.active_seconds)

    @api.multi
    def unlink(self):

        self.mapped('dried_oven_ids').write({
            'is_in_use': False
        })
        return super(OvenUse, self).unlink()

    @api.multi
    def init_process(self):
        for item in self:
            if item.init_date:
                raise models.ValidationError('este proceso ya ha sido iniciado')
            if not item.dried_oven_ids:
                raise models.ValidationError('Debe seleccionar el horno a iniciar')
            if not item.used_lot_id:
                raise models.ValidationError('Debe Seleccionar un lote a secar')
            item.init_date = datetime.utcnow()
            item.init_active_time = item.init_date.timestamp()
            item.unpelled_dried_id.state = 'progress'
            item.dried_oven_ids.update({
                'is_in_use': True
            })
            item.used_lot_id.unpelled_state = 'drying'

    @api.multi
    def pause_process(self):
        for item in self:
            item.finish_active_time = datetime.utcnow().timestamp()
            item.active_seconds += item.finish_active_time - item.init_active_time

    @api.multi
    def resume_process(self):
        for item in self:
            item.init_active_time = datetime.utcnow().timestamp()
            item.finish_active_time = 0

    @api.multi
    def finish_process(self):
        for item in self:
            if item.used_lot_id and item.used_lot_id.reception_state != 'done':
                raise models.ValidationError(
                    'la recepción del lote {} no se encuentra en estado realizado. '
                    'Primero termine el proceso de recepción'.format(item.used_lot_id.name))
            item.finish_date = datetime.utcnow()
            if item.finish_active_time == 0:
                item.finish_active_time = item.finish_date.timestamp()
                item.active_seconds += item.finish_active_time - item.init_active_time
            for dried_oven_id in item.dried_oven_ids:
                models._logger.error(item.unpelled_dried_id.oven_use_ids.filtered(
                    lambda a: a.id != item.id and dried_oven_id in a.dried_oven_ids and not a.finish_date
                ))
                if not item.unpelled_dried_id.oven_use_ids.filtered(
                    lambda a: a.id != item.id and dried_oven_id in a.dried_oven_ids and not a.finish_date
                ):
                    raise models.ValidationError('entró')
                    dried_oven_id.update({
                        'is_in_use': False
                    })

    @api.multi
    def print_oven_label(self):
        for item in self:
            return self.env.ref('dimabe_manufacturing.action_oven_use_label_report') \
                .report_action(item)

    @api.multi
    def get_full_url(self):
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return base_url
