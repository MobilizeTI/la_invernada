from odoo import models, fields, api
import datetime
from datetime import datetime, date, time


class CustomSettlement(models.Model):
    _name = 'custom.settlement'
    employee_id = fields.Many2one('hr.employee','Empleado',required=True)

    contract_id = fields.Many2one('hr.contract', 'Contrato', related='employee_id.contract_id')

    fired_id = fields.Many2one('custom.fired', 'Causal de Despido')

    date_start_contract = fields.Date('Fecha de inicio', related='contract_id.date_start')

    date_of_notification = fields.Date('Fecha de Notificacion de despido')

    date_settlement = fields.Date('Fecha finiquito')

    period_of_service = fields.Float('Periodo de servicio')

    @api.multi
    def test(self):
        for item in self:
            difference = datetime.now().year - item.date_start_contract.year
            if difference > 0:
                item.period_of_service = difference
                raise models.ValidationError(difference)
            else:
                difference_month = (datetime.now().month - item.date_start_contract.month) / 100
                item.period_of_service = difference_month
                raise models.ValidationError(difference_month)



