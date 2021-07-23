from odoo import api, models


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self, auto_commit=False):
        context = self._context.copy()
        custom_layout = context.get('custom_layout')
        force_custom_layout = ""
        if self.env.user.company_id.mail_layout_view_id:
            if self.env.user.company_id.force_notify_layout or not custom_layout:
                force_custom_layout = self.env.user.company_id.mail_layout_view_id.key
        if self.template_id.mail_layout_view_id:
            force_custom_layout = self.template_id.mail_layout_view_id.key
        if force_custom_layout:
            try:
                self.env.ref(force_custom_layout, False)
                self = self.with_context(custom_layout=force_custom_layout)
            except Exception:
                pass
        return super(MailComposeMessage, self).send_mail(auto_commit=auto_commit)
