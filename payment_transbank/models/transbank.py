from odoo import api, fields, models, _
from odoo.tools import float_round
from odoo.tools.float_utils import float_repr

from .cli import TransbankCertificate
import unicodedata


class PaymentAcquirerTransbank(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('transbank', 'Transbank')])
    environment = fields.Selection(selection_add=[('cert', 'Certification')], default="test")

    # Elementos para generar el certificado
    commerce_id = fields.Char(string='ID de comercio',
        default="597020000541",
        help="Es requerido para que funcione el addons y generar el certificado autofirmado")
    city = fields.Char(string="Ciudad", help="Debe ser en mayúscula y sin tílde")
    certificate = fields.Text(string="Certificado", help="Copiar y pegar este texto. Guardar con extensión [nombre_archivo].crt")
    
    @api.one
    def generate_certificate(self):
        city = ''.join((c for c in unicodedata.normalize('NFD', self.city.upper()) if unicodedata.category(c) != 'Mn'))
        # Crear llave privada
        tbk = TransbankCertificate()
        pkey = tbk.createKeys(TransbankCertificate.TYPE_RSA, 2048)
        # Generar certificado
        cert = tbk.createCert(pkey, C='CL', L=city, CN=self.commerce_id)
        # Firmar certificado
        signed_cert = tbk.signCert(cert, (cert, pkey), (0, (365*24*60*60*4)))
        # Guardar certificados
        tbk.saveCert(pkey, signed_cert, self.commerce_id)
        #desplegar clave pública
        self.write({'certificate': tbk.certificate})

    def _get_feature_support(self):
        res = super(PaymentAcquirerTransbank, self)._get_feature_support()
        res['fees'].append('transbank')
        res['authorize'].append('transbank')
        #res['tokenize'].append('transbank')
        return res
    
    def transbank_get_form_action_url(self):
        return '/payment/transbank/init'
    
    #@TDETODO: aqui llega el pedido desde el web
    def transbank_form_generate_values(self, values):
        amount = float_repr(float_round(values['amount'], 2), 0)
        currency = values['currency'] and values['currency'].name or ''
        buyorder = values['reference']
        acquirer_id = self.id

        transbank_tx_values = dict(values)
        temp_transbank_tx_values = {
            'ACQUIRER_ID': acquirer_id,
            'AMOUNT': amount,
            'CURRENCY': currency,
            'BUYORDER': buyorder
        }
        transbank_tx_values.update(temp_transbank_tx_values)
        return transbank_tx_values
    
    @api.multi
    def toggle_environment_value(self):
        #prod = self.filtered(lambda acquirer: acquirer.environment == 'prod')
        #prod.write({'environment': 'test'})
        #(self-prod).write({'environment': 'prod'})
        if self.provider=='transbank':
            if self.environment=='test':
                self.write({'environment': 'cert'})
            elif self.environment=='cert':
                self.write({'environment': 'prod'})
            elif self.environment=='prod':
                self.write({'environment': 'test'})
        else:
            super(PaymentAcquirerTransbank, self).toggle_environment_value()

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'
    
    transbank_auth_transaction = fields.Char("Código autorización de transacción", readonly=True, copy=False)
    transbank_payment_type = fields.Char("Tipo de pago", readonly=True, copy=False)
    transbank_fee_type = fields.Char("Numero de cuotas", readonly=True, copy=False)
    transbank_amount_fee = fields.Char("Valor de cuota", readonly=True, copy=False)
    transbank_last_digits = fields.Char("Últimos dígitos de la tarjeta", readonly=True, copy=False)
    transbank_commerce_id = fields.Char(string='ID de comercio')
    
    @api.multi
    def action_capture(self):
        transaction_transbank = self.filtered(lambda x: x.transbank_auth_transaction)
        for transaction in transaction_transbank:
            if transaction.state != 'done':
                transaction.sudo()._set_transaction_done()
        return super(PaymentTransaction, self-transaction_transbank).action_capture()
    
    def render_sale_button(self, order, submit_txt=None, render_values=None):
        if not render_values is None:
            render_values['transbank_order_id'] = order.id
            render_values['transbank_transaction_id'] = self.id
        return super(PaymentTransaction, self).render_sale_button(order, submit_txt=submit_txt, render_values=render_values)

# TODO: eliminar tabla, los  campos se pasaron a payment_transaction
class SaleOrderTxTransbank(models.Model):
    _name = 'payment.transbank'
    _description = 'Transbank transaction' 

    order_id = fields.Many2one('sale.order', "Sale orders")
    auth_transaction = fields.Char("Código autorización de transacción")
    payment_type = fields.Char("Tipo de pago")
    fee_type = fields.Char("Numero de cuotas")
    amount_fee = fields.Char("Valor de cuota")
    last_digits = fields.Char("Últimos dígitos de la tarjeta")
    token_ws = fields.Char("Token")
    buyorder = fields.Char("Orden de compra")

class SaleOrder(models.Model):
    _inherit="sale.order"

    tbk_id = fields.One2many('payment.transbank', 'order_id', 'Transbank payment')
