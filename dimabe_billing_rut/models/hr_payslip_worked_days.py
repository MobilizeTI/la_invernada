from odoo import fields, models, api


class HrPaySlipWorkedDay (models.Model):
    _inherit = 'hr.payslip.worked_days'
    _description = 'Description'

    unpaid = fields.Boolean('No Pagado')
    


