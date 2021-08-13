from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class AccountJournal(models.Model):
    _inherit = 'account.journal'
    
    @api.model
    def default_get(self, fields_list):
        values = super(AccountJournal, self).default_get(fields_list)
        values['update_posted'] = True
        return values
    
    @api.model
    def enable_cancel_entries(self):
        #permitir cancelar por defecto a los diarios creados
        self.search([('update_posted','=',False)]).write({'update_posted': True})
        #importacion de extractos bancarios sea manual por defecto
        #sincronizacion en linea es para enterprise
        self.search([]).write({'bank_statements_source': 'undefined'})
        return True
