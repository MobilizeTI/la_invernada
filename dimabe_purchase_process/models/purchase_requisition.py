from odoo import fields, models, api


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    @api.model
    def create(self, vals_list):
        if not vals_list['ordering_date']:
            vals_list['ordering_date'] = fields.datetime.now()
        return super(PurchaseRequisition, self).create(vals_list)

    @api.multi
    def action_in_progress(self):
        self.ensure_one()
        res = super(PurchaseRequisition, self).action_in_progress()
        template_id = self.env.ref('dimabe_purchase_process.new_requisition_mail_template')
        self.message_post_with_template(template_id.id)
        return res

    @api.multi
    def action_open(self):
        self.ensure_one()
        res = super(PurchaseRequisition, self).action_open()
        template_id = self.env.ref('dimabe_purchase_process.budget_ready_mail_template')
        self.message_post_with_template(template_id.id)
        return res


    @api.model
    def get_email_to(self, ref_id):
        user_group = self.env.ref(ref_id)
        email_list = [
            usr.partner_id.email for usr in user_group.users if usr.partner_id.email
        ]
        return ','.join(email_list)
