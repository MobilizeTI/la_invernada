from odoo import models, api, fields
from dateutil.relativedelta import *
import pandas as pd
from odoo.addons import decimal_precision as dp
import xlsxwriter
import xlwt
from xlsxwriter.workbook import Workbook
import base64

import io
import re


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    salary_id = fields.Many2one('hr.salary.rule', 'Agregar Entrada')

    have_absence = fields.Boolean('¿Tiene Ausencias?', default=False)

    absence_days = fields.Float('Dias Ausencias', default=0)

    vacations_days = fields.Float('Dias Vacaciones', default=0)

    vacation_paid = fields.Boolean('Vacaciones Pagadas')

    total_imp = fields.Float('Total Imp. Anterior')

    account_analytic_id = fields.Many2one('account.analytic.account','Centro de Costo',readonly=True)


    @api.onchange('struct_id')
    def onchange_domain(self):
        res = {
            'domain': {
                'salary_id': [('name', 'not in', self.input_line_ids.mapped('name'))],
            }
        }
        return res

    @api.multi
    def add(self):
        for item in self:
            if item.salary_id:
                self.env['hr.payslip.input'].create({
                    'name': item.salary_id.name,
                    'code': item.salary_id.code,
                    'contract_id': item.contract_id.id,
                    'payslip_id': item.id
                })
            item.salary_id = None

    @api.multi
    def get_leave(self):
        for item in self:
            employee_id = item.contract_id.employee_id
            leaves = self.env['hr.leave'].search(
                [('employee_id', '=', employee_id.id), ('state', '=', 'validate'),
                 ('date_from', '>', item.date_from), ('date_to', '<', item.date_to)])
            for leave in leaves:
                if item.worked_days_line_ids.filtered(
                        lambda a: a.name == leave.holiday_status_id.name).number_of_days != sum(
                    leaves.mapped('number_of_days')):
                    models._logger.error('Aqui')
                    if leave.holiday_status_id.name in item.worked_days_line_ids.mapped('name'):

                        days = item.worked_days_line_ids.filtered(lambda a: a.name == leave.holiday_status_id.name)
                        days.write({
                            'number_of_days': days.number_of_days + leave.number_of_days
                        })
                    else:
                        models._logger.error('No Aqui')
                        code = self.generate_code(leave.holiday_status_id.name, leave.holiday_status_id.id)
                        self.env['hr.payslip.worked_days'].create({
                            'name': leave.holiday_status_id.name,
                            'number_of_days': leave.number_of_days,
                            'code': code,
                            'contract_id': item.contract_id.id,
                            'payslip_id': item.id,
                            'unpaid': leave.holiday_status_id.unpaid
                        })
                if leave.holiday_status_id.name == 'Vacaciones' and leaves:
                    models._logger.error('Esta Aqui')
                    if leave.holiday_status_id.unpaid:
                        item.write({
                            'vacations_days': sum(
                                item.worked_days_line_ids.filtered(lambda a: 'Vacaciones' in a.name).mapped(
                                    'number_of_days')),
                            'vacation_paid': False
                        })
                    else:
                        models._logger.error('Aqui Esta')
                        item.write({
                            'vacations_days': sum(
                                item.worked_days_line_ids.filtered(lambda a: 'Vacaciones' in a.name).mapped(
                                    'number_of_days')),
                            'vacation_paid': True
                        })
            if sum(leaves.mapped('number_of_days')) > 0 and not leaves:
                models._logger.error('No')
                item.write({
                    'absence_days': 0,
                    'have_absence': False
                })
            else:
                item.write({
                    'absence_days': sum(leaves.filtered(lambda a: 'Vacaciones' not in a.holiday_status_id.name).mapped(
                        'number_of_days')),
                    'have_absence': True
                })

    def generate_code(self, name, id):
        res = re.sub(r'[AEIOUÜÁÉÍÓÚ]', '', name, flags=re.IGNORECASE)
        identy = ''
        if id > 10:
            identy = '{}0'.format(id)
        else:
            identy = '{}00'.format(id)
        res = res[0:3].upper() + identy
        return res

    @api.multi
    def write(self,vals):
        vals['account_analytic_id'] = self.contract_id.department_id.analytic_account_id.id
        return super(HrPayslip,self).write(vals)

    @api.multi
    def compute_sheet(self):
        res = super(HrPayslip, self).compute_sheet()
        self.write({
            'account_analytic_id':self.contract_id.department_id.analytic_account_id.id
        })
        if self.worked_days_line_ids.filtered(lambda a: a.code == 'SBS220') and self.line_ids.filtered(
                lambda a: a.code == 'TOTIM').total == 0:
            payslips = self.env['hr.payslip'].search([('employee_id', '=', self.employee_id.id)])
            if payslips.mapped('worked_days_line_ids').filtered(lambda a: a.code == 'WORK100').filtered(
                    lambda a: a.number_of_days == 30):
                worked_days = payslips.mapped('worked_days_line_ids').filtered(lambda a: a.code == 'WORK100').filtered(
                    lambda a: a.number_of_days == 30)[-1]
                wage = worked_days.payslip_id.mapped('line_ids').filtered(lambda a: a.code == 'SUELDO').total
            else:
                wage = self.contract_id.wage
            day_value = wage / 30
            licencies_days = self.worked_days_line_ids.filtered(lambda a: a.code == 'SBS220').number_of_days
            sis_value = self.get_sis_values(self.contract_id.afp_id.name, self.id)
            value = ((day_value * licencies_days) * sis_value) / 100
            self.line_ids.filtered(lambda a: a.code == 'SIS').write({
                'total': value,
                'amount': value
            })
            afc_percentaje = 3 if self.contract_id.type_id.name == 'Plazo Fijo' or self.contract_id.type_id.name == 'Operario de Produccion' else 2.4
            afc_value = ((day_value * licencies_days) * afc_percentaje) / 100
            self.line_ids.filtered(lambda a: a.code == 'SECEEMP').write({
                'total': afc_value,
                'amount': afc_value
            })
            return res
        elif self.worked_days_line_ids.filtered(lambda a: a.code == 'SBS220'):
            day_value = self.line_ids.filtered(lambda a: a.code == 'SUELDO').total / 30
            licencies_days = self.worked_days_line_ids.filtered(lambda a: a.code == 'SBS220').number_of_days
            sis_value = self.get_sis_values(self.contract_id.afp_id.name, self.id)
            value = ((day_value * licencies_days) * sis_value) / 100
            self.line_ids.filtered(lambda a: a.code == 'SIS').write({
                'total': value,
                'amount': value
            })
            afc_percentaje = 3 if self.contract_id.type_id.name == 'Plazo Fijo' or self.contract_id.type_id.name == 'Operario de Produccion' else 2.4
            afc_value = ((day_value * licencies_days) * afc_percentaje) / 100
            self.line_ids.filtered(lambda a: a.code == 'SECEEMP').write({
                'total': afc_value,
                'amount': afc_value
            })
            return res
        else:
            return res

    def get_sis_values(self, afp, payslip_id):
        payslip = self.env['hr.payslip'].search([('id', '=', payslip_id)])
        if afp == 'CAPITAL':
            return payslip.indicadores_id.tasa_sis_capital
        elif afp == 'CUPRUM':
            return payslip.indicadores_id.tasa_sis_cuprum
        elif afp == 'HABITAT':
            return payslip.indicadores_id.tasa_sis_habitat
        elif afp == 'MODELO':
            return payslip.indicadores_id.tasa_sis_modelo
        elif afp == 'PLANVITAL':
            return payslip.indicadores_id.tasa_sis_planvital
        elif afp == 'PROVIDA':
            return payslip.indicadores_id.tasa_sis_provida
        elif afp == 'UNO':
            return payslip.indicadores_id.tasa_sis_uno
        else:
            return 0

