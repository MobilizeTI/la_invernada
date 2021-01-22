from odoo import models, fields, api


class CustomMutuality(models.Model):
    _name = 'custom.mutuality'

    company_id = fields.Many2one('res.partner', 'Compañia', domain=lambda self: [
        ('id', 'in', self.env['hr.employee'].sudo().search([('active', '=', True)]).mapped('address_id').mapped('id'))])

    value = fields.Float('Valor')

    indicator_id = fields.Many2one(comodel_name='hr.indicadores', auto_join=True, string='Indicadores')
