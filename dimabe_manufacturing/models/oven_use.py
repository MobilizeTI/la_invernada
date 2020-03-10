from odoo import fields, models, api, _
from datetime import datetime
from ..helpers import date_helper


class OvenUse(models.Model):
    _name = 'oven.use'
    _description = 'datos de uso de los hornos'

    ready_to_close = fields.Boolean('Cerrar')

    name = fields.Char(
        'Horno en uso',
        compute='_compute_name'
    )

    done = fields.Boolean('Listo')

    init_date = fields.Datetime('Inicio de Proceso')

    finish_date = fields.Datetime('Termino de Proceso')

    active_seconds = fields.Integer('Segundos de Actividad')

    active_time = fields.Char(
        'Tiempo Transcurrido',
        compute='_compute_active_time',
        store=True
    )

    used_lot_id = fields.Many2one(
        'stock.production.lot',
        'Lote a Secar'
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

    @api.multi
    def _compute_name(self):
        for item in self:
            for name in item.dried_oven_ids.mapped('name'):
                item.name += '{} '.format(name)
            models._logger.error(item.name)

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
            item.dried_oven_ids.update({
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
