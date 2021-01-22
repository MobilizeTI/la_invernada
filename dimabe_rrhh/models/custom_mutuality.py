from odoo import models, fields, api


class CustomMutuality(models.Model):
    _name = 'custom.mutuality'

    company_id = fields.Many2one('res.partner','Compañia')

    value = fields.Float('Valor')

    indicator_id = fields.Many2one(comodel_name='hr.indicadores',auto_join=True,string='Indicadores')

    partner_ids = fields.Many2many(comodel_name='res.partner',compute='compute_partner_company')

    @api.multi
    def compute_partner_company(self):
        for item in self:
            hr_employee = self.env['hr.employee'].sudo().search([])
            companies = self.env['res.partner'].sudo().search([('id','in',hr_employee.mapped('id'))])
            self.partner_ids = companies




