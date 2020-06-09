from odoo import fields, models, api


class ChangeProductionQty(models.TransientModel):
    _inherit = 'change.production.qty'

    # @api.multi
    # def change_prod_qty(self):
    #     raise models.ValidationError('Opción no disponible')
    #     return {}