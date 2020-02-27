from odoo import fields, models, api


class OvenUse(models.Model):
    _name = 'oven.use'
    _description = 'datos de uso de los hornos'

    init_date = fields.Datetime('Inicio de Proceso')

    finish_date = fields.Datetime('Termino de Proceso')

    active_seconds = fields.Integer('Segundos de Actividad')

    init_active_date = fields.Integer('Inicio de tiempo activo')

    finish_active_time = fields.Integer('Fin de tiempo activo')

    dried_oven_id = fields.Many2one('dried.oven', 'horno')

    unpelled_dried_id = fields.Many2one('unpelled.dried', 'Proceso de secado')
