from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'
    
    @api.noguess
    def report_action(self, docids, data=None, config=True):
        # pasar config=False para que no haga verificacion del logo de la company
        return super(IrActionsReport, self).report_action(docids, data=data, config=False)