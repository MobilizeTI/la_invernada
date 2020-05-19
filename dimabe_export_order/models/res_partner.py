from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_agent = fields.Boolean('Es Agente')



    client_identifier_id = fields.Many2one(
        'custom.client.identifier',
        'Tipo de Identificador'
    )

    client_identifier_value = fields.Char('Valor Identificador')

    company_type = fields.Selection(string='Company Type',
                                    selection=[('person', 'Individual'), ('company', 'Company')],
                                    default='company',
                                    compute='_compute_company_type',
                                    inverse='_write_company_type'
                                    )


