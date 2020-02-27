from odoo import fields, models, api
from datetime import datetime


class OvenUse(models.Model):
    _name = 'oven.use'
    _description = 'datos de uso de los hornos'

    name = fields.Char(
        'Horno en uso',
        related='dried_oven_id.name'
    )

    init_date = fields.Datetime('Inicio de Proceso')

    finish_date = fields.Datetime('Termino de Proceso')

    active_seconds = fields.Integer('Segundos de Actividad')

    init_active_date = fields.Integer('Inicio de tiempo activo')

    finish_active_time = fields.Integer('Fin de tiempo activo')

    dried_oven_id = fields.Many2one('dried.oven', 'horno')

    unpelled_dried_id = fields.Many2one('unpelled.dried', 'Proceso de secado')

    @api.model
    def init_process(self):
        if self.init_date:
            raise models.ValidationError('este proceso ya ha sido iniciado')
        self.init_date = datetime.utcnow()
