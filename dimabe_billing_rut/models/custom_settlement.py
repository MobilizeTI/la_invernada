from odoo import models, fields, api
import datetime
from datetime import datetime, date, time
from dateutil.relativedelta import *


class CustomSettlement(models.Model):
    _name = 'custom.settlement'
    employee_id = fields.Many2one('hr.employee', 'Empleado', required=True)

    contract_id = fields.Many2one('hr.contract', 'Contrato', related='employee_id.contract_id')

    fired_id = fields.Many2one('custom.fired', 'Causal de Despido')

    date_start_contract = fields.Date('Fecha de inicio', related='contract_id.date_start')

    date_of_notification = fields.Date('Fecha de Notificacion de despido')

    date_settlement = fields.Date('Fecha finiquito')

    period_of_service = fields.Char('Periodo de servicio', compute='compute_period', readonly=True)

    vacation_day = fields.Float('Dias de Vacaciones',compute='compute_vacation_day')

    @api.multi
    @api.onchange('date_settlement')
    def compute_period(self):
        for item in self:
            period = relativedelta(item.date_settlement, item.date_start_contract)
            item.period_of_service = '{} años , {} meses , {} dias'.format(period.years, period.months, period.days)

    @api.multi
    @api.onchange('date_settlement')
    def compute_vacation_day(self):
        for item in self:
            period = relativedelta(item.date_settlement, item.date_start_contract)
            item.vacaction_day = period.years
