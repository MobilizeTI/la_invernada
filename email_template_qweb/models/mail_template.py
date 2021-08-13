# Copyright 2016 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import api, fields, tools, models

_logger = logging.getLogger(__name__)

class MailTemplate(models.Model):
    _inherit = 'mail.template'

    body_type = fields.Selection(
        [('jinja2', 'Jinja2'), ('qweb', 'QWeb')], 'Body templating engine',
        default='jinja2', required=True)
    body_view_id = fields.Many2one(
        'ir.ui.view', 'Body view', domain=[('type', '=', 'qweb')])
    body_view_arch = fields.Text(related='body_view_id.arch')
    mail_layout_view_id = fields.Many2one(
        'ir.ui.view', 'Notify Layout',
        domain=[('type', '=', 'qweb'), ('name', 'ilike', 'mail_notification')])
    
    @api.multi
    def get_parser(self):
        """
        El parser debe llamarse mail.<template_name>.parser y estar cargado al registro del sistema
        """
        parser = self.env.get("mail.%s.parser" % self.body_view_id.name)
        if parser is None:
            parser = self.env.get('mail.template.parser')
        return parser

    @api.multi
    def generate_email(self, res_ids, fields=None):
        multi_mode = True
        if isinstance(res_ids, int):
            res_ids = [res_ids]
            multi_mode = False
        result = super(MailTemplate, self).generate_email(
            res_ids, fields=fields
        )
        for res_id, template in self.get_email_template(res_ids).items():
            if template.body_type == 'qweb' and\
                    (not fields or 'body_html' in fields):
                for record in self.env[template.model].browse(res_id):
                    template_values = {
                        'object': record,
                        'email_template': template,
                    }
                    parser_temp = template.get_parser()
                    #si existe el registro, enviar a actualizar los datos de ser necesario
                    if parser_temp is not None:
                        ctx = parser_temp.get_initial_context(template, record)
                        parser_values = parser_temp.with_context(ctx).get_values(template, record)
                        template_values.update(parser_values)
                        attachments = parser_temp.with_context(ctx).create_attachments(template, record, parser_values)
                        for attachment in attachments:
                            result[res_id].setdefault('attachment_ids', []).append(attachment.id)
                    body_html = template.body_view_id.render(template_values)
                    # Some wizards, like when sending a sales order, need this
                    # fix to display accents correctly
                    body_html = tools.ustr(body_html)
                    result[res_id]['body_html'] = self.render_post_process(
                        body_html
                    )
                    result[res_id]['body'] = tools.html_sanitize(
                        result[res_id]['body_html']
                    )
        return multi_mode and result or result[res_ids[0]]

    @api.multi
    def action_sent_mail(self, record):
        MailComposeMessage = self.env['mail.compose.message']
        ctx = self.env.context.copy()
        if 'custom_layout' not in ctx:
            ctx['custom_layout'] = "mail.mail_notification_borders"
        if 'mail_notify_force_send' not in ctx:
            ctx['mail_notify_force_send'] = True
        if 'show_no_response' not in ctx:
            ctx['show_no_response'] = True
        ctx.update(
            default_model=record._name,
            default_res_id=record.id,
            default_use_template=bool(self),
            default_template_id=self.id,
            default_composition_mode='comment',
        )
        msj = MailComposeMessage.with_context(ctx).create({})
        send_mail = True
        try:
            msj.onchange_template_id_wrapper()
            msj.send_mail()
        except Exception as ex:
            _logger.error(tools.ustr(ex))
            send_mail = False
        return send_mail
