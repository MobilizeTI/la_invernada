from odoo import models, api

from . import css_styles 

class MailTemplateParser(models.AbstractModel):

    _name = 'mail.template.parser'
    _description = 'Parser de Plantiillas de correo'
    
    @api.model
    def get_initial_context(self, template, record):
        return self.env.context.copy()
    
    @api.model
    def get_values(self, template, record):
        return {'css_class': css_styles.styles.copy()}
    
    @api.model
    def get_attachments_values(self, template, record, values):
        return []
    
    @api.model
    def get_attachments(self, template, record):
        '''
        :return: An ir.attachment recordset
        '''
        if not template.body_view_id:
            return []
        domain = [
            ('res_id', '=', record.id),
            ('res_model', '=', record._name),
            ('description', '=', template.body_view_id.name),
        ]
        return self.env['ir.attachment'].search(domain)

    @api.model
    def create_attachments(self, template, record, values):
        '''
        Crear adjuntos de ser necesarios
        '''
        attachment_model = self.env['ir.attachment']
        attachments = self.env['ir.attachment'].browse()
        attachments_to_unlink = self.get_attachments(template, record)
        if attachments_to_unlink:
            attachments_to_unlink.unlink()
        attachments_values = self.get_attachments_values(template, record, values)
        for value in attachments_values:
            attachments |= attachment_model.create(value)
        return attachments
