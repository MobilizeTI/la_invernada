from odoo import models, fields, api
import datetime


class CustomSettlement(models.Model):
    _name = 'custom.settlement'
    employee_id = fields.Many2one('hr.employee')


    contract_id = fields.Many2one('hr.contract', 'Contrato',related='employee_id.contract_id')

    fired_id = fields.Many2one('custom.fired', 'Causal de Despido')

    date_start_contract = fields.Date('Fecha de inicio', related='contract_id.date_start')

    date_of_notification = fields.Date('Fecha de Notificacion de despido')

    date_settlement = fields.Date('Fecha finiquito')

    period_of_service = fields.Float('Periodo de servicio')

    @api.multi
    def test(self):
        for item in self:
            date = datetime.datetime.strftime(item.date_start_contract,"%Y-%m-%d")
            raise models.ValidationError(date.month)





