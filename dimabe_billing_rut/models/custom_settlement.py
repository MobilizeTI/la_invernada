from odoo import models, fields, api
from datetime import date, timedelta
from dateutil.relativedelta import *
import pandas as pd


class CustomSettlement(models.Model):
    _name = 'custom.settlement'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', 'Empleado', required=True)

    contract_id = fields.Many2one('hr.contract', 'Contrato', related='employee_id.contract_id')

    fired_id = fields.Many2one('custom.fired', 'Causal de Despido', required=True)

    article_causal = fields.Selection('Articulo', related='fired_id.article')

    date_start_contract = fields.Date('Fecha de inicio', related='contract_id.date_start')

    date_of_notification = fields.Date('Fecha de Notificacion de despido', default=date.today())

    date_settlement = fields.Date('Fecha finiquito', required=True)

    period_of_service = fields.Char('Periodo de servicio', compute='compute_period', readonly=True)

    vacation_days = fields.Float('Dias de Vacaciones', compute='compute_vacation_day', readonly=True)

    day_takes = fields.Float('Dias Tomados', default=0.0)
    days_pending = fields.Float('Dias Pendiente', compute='compute_days_pending')

    non_working_days = fields.Integer('Dias Inhabiles', compute='compute_no_working_days')

    type_contract = fields.Selection([
        ('Fijo', 'Fijo'),
        ('Variable', 'Variable')
    ])

    currency_id = fields.Many2one('res.currency', string='Moneda')

    wage = fields.Monetary('Sueldo Base', related='contract_id.wage', currency_field='currency_id')

    reward_value = fields.Monetary('Gratificacion', compute='compute_reward')

    reward_selection = fields.Selection([
        ('Yes', 'Si'),
        ('No', 'No'),
        ('Edit', 'Editar')
    ], default='Yes')

    snack_bonus = fields.Float('Colacion')

    mobilization_bonus = fields.Float('Movilizacion')

    pending_remuneration_payment = fields.Monetary('Remuneraciones Pendientes')

    compensation_warning = fields.Monetary('indemnización Aviso Previo', compute='compute_warning')

    compensation_years = fields.Monetary('indemnización Años de Servicio', compute='compute_years')

    compensation_vacations = fields.Monetary('indemnización Vacaciones', compute='compute_vacations')

    settlement = fields.Monetary('Finiquito')

    @api.multi
    @api.onchange('day_takes')
    def compute_days_pending(self):
        for item in self:
            item.days_pending = (round(item.vacation_days) - item.day_takes) + item.non_working_days

    @api.multi
    @api.onchange('date_settlement')
    def compute_period(self):
        for item in self:
            period = relativedelta(item.date_settlement, item.date_start_contract)
            item.period_of_service = '{} años , {} meses , {} dias'.format(period.years, period.months,
                                                                           (period.days + 1))

    @api.multi
    @api.onchange('date_settlement')
    def compute_vacation_day(self):
        for item in self:
            period = relativedelta(item.date_settlement, item.date_start_contract)
            item.vacation_days = (15 * period.years + (period.months * 1.25 + (period.days + 1) / 30 * 1.25))

    @api.multi
    @api.onchange('reward_selection')
    def compute_reward(self):
        for item in self:
            if item.reward_selection == 'Yes' or item.reward_selection == 'Edit':
                item.reward_value = round(item.wage * 0.25)
            else:
                item.reward_value = 0

    @api.multi
    def compute_vacations(self):
        for item in self:
            if self.article_causal != '161':
                if item.vacation_days > 0:
                    daily = (item.wage + item.reward_value) / 30
                    item.compensation_vacations = item.days_pending * daily
            else:
                item.compensation_vacations = 0.0

    @api.multi
    @api.onchange('date_of_notification')
    def compute_warning(self):
        for item in self:
            if item.date_settlement:
                warning = abs(self.date_of_notification - self.date_settlement).days
                if warning < 30:
                    item.compensation_warning = round(
                        (item.wage + item.reward_value) + (item.snack_bonus + item.mobilization_bonus))

    @api.multi
    @api.onchange('date_settlement')
    def compute_years(self):
        for item in self:
            period = relativedelta(item.date_settlement, item.date_start_contract)
            item.compensation_years = round((item.wage + item.reward_value) + (
                    item.snack_bonus + item.mobilization_bonus)) * period.years

    @api.multi
    @api.onchange('date_settlement')
    def compute_no_working_days(self):
        for item in self:
            item.non_working_days = item.get_weekend()

    @api.multi
    @api.depends('date_settlement', 'pending_remuneration_payment', 'reward_selection')
    def calculate_settlement(self):
        for item in self:
            period = relativedelta(item.date_settlement, item.date_start_contract)
            item.settlement = (item.wage + item.reward_value) + item.pending_remuneration_payment + \
                              (item.snack_bonus + item.mobilization_bonus) \
                              + (item.compensation_vacations + item.compensation_warning + item.compensation_years)

    @api.multi
    def test(self):
        weekend = self.get_weekend()
        days = round(self.vacation_days)
        date_after = self.date_settlement + timedelta(days=days)
        date_settlement = self.date_settlement + timedelta(days=1)
        holiday = self.env['custom.holidays'].search([('date', '>', date_settlement), ('date', '<', date_after)])
        raise models.UserError(len(holiday))

    def get_weekend(self):
        days = round(self.vacation_days)
        date_after = self.date_settlement + timedelta(days=days)
        date_settlement = self.date_settlement + timedelta(days=1)
        saturdays = pd.date_range(start=date_settlement, end=date_after, freq='W-SAT').strftime('%m/%d/%Y').tolist()
        models._logger.error(saturdays)
        sundays = pd.date_range(start=date_settlement, end=date_after, freq='W-SUN').strftime('%m/%d/%Y').tolist()
        models._logger.error(sundays)
        holiday = self.env['custom.holidays'].search([('date', '>', date_settlement), ('date', '<', date_after)])
        weeekend = sorted(sorted(saturdays) + sorted(sundays))
        return len(weeekend) + len(holiday)
