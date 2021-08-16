from odoo import models, api, fields, tools


class OdooUtils(models.AbstractModel):
    _inherit = 'odoo.utils'
    
    @api.model
    def set_system_data_init(self):
        '''
        Configurar el nombre del sistema por defecto por medio de parametros
        '''
        Params = self.env['ir.config_parameter'].sudo()
        parameters = [
            ('web_debranding.new_name', 'Retail Chile'), 
            ('web_debranding.new_title', 'Retail Chile'), 
            ('web_debranding.new_website', 'https://intersport.cl'),
            ('web_m2x_options.create', 'False'),
        ]
        for param, default in parameters:
            Params.set_param(param, default or ' ')
        users = self.env['res.users'].with_context(active_test=False).search([])
        users.write({'tz': 'America/Santiago'})
