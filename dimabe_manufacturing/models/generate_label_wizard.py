from odoo import fields, models, api
import base64

class GenerateLabelWizard(models.TransientModel):
    _name = 'generate.label.wizard'

    eco_id = fields.Many2one('mrp.eco')

    product_id = fields.Many2one('product.product', related='eco_id.product_id')

    producer_id = fields.Many2one('res.partner', string='Productor')

    is_real_best_date = fields.Boolean('Se usara una fecha real')

    best_before_date_mask = fields.Char(string="Consumir Preferentemente antes de")

    best_before_date = fields.Date(string='Consumir Preferentemente antes de')

    is_real_packaging_date = fields.Boolean('Se usara una fecha real')

    packaging_date_mask = fields.Char(string='Fecha de Envasado')

    packaging_date = fields.Date(string='Fecha de Envasado')

    is_real_order = fields.Boolean(string='Se usara un pedido real')

    sale_order_id = fields.Many2one('sale.order',string='Codigo de Trazabilidad')

    trace_code = fields.Char(string='Codigo de Trazabilidad')

    @api.multi
    def generate_label(self):
        label = self
        report = self.env.ref('dimabe_manufacturing.action_stock_production_lot_serial_label_report_template')
        ctx = self.env.context.copy()
        ctx['flag'] = True
        pdf = report.with_context(ctx).render_qweb_pdf(label.id)
        file = base64.b64encode(pdf[0])
        attachment_id = self.env['ir.attachment'].sudo().create({
            'name': "Prueba",
            'datas_fname': "Prueba",
            'datas': file
        })
        action = {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}?download=true'.format(attachment_id.id, ),
            'target': 'current',
        }
        return action