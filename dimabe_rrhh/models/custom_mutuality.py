from odoo import models, fields, api


class CustomMutuality(models.Model):
    _name = 'custom.mutuality'

    company_id = fields.Many2one('res.company','Compañia')

    value = fields.Float('Valor')

    indicator_id = fields.Many2one(comodel_name='hr.indicadores',auto_join=True,string='Indicadores')




