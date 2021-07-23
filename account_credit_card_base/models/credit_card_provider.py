from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class CreditCardProvider(models.Model):
    _name = 'credit.card.provider'
    _description = 'Grupos de tarjetas de credito'
    _order = 'sequence'
    
    name = fields.Char(string='Nombre', required=True)
    report_format = fields.Selection([
        ('name','Nombre'),
        ('code','Codigo'),
        ], string='Mostrar en reporte', default='name', 
        help="En reporte de cuadratura de tiendas indica si se imprime el nombre del diairo o el codigo",)
    sequence = fields.Integer('Secuencia', default=10)
    active = fields.Boolean(u'Active?', default=True)
