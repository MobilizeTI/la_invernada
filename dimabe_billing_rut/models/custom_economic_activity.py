from odoo import models, fields

class CustomEconomicActivity(models.Model):
    _name = 'custom.economic.activity'

    code = fields.Char(string='Código Actividad')
    name = fields.Char(string='Nombre Actividad')
    tax_affect = fields.Char(string='Afecto a IVA')
    tax_category = fields.Char(string='Categoría Tributaria')
    is_active = fields.Boolean(default=True)

    