import urllib.parse
import werkzeug

from odoo import http, SUPERUSER_ID
from odoo.http import request

from ..certificates import cert_normal
from ..data.configuration import Configuration
from ..data.webpay import Webpay
from ..data.transbank import RESPONSE_CODE, PAYMENT_TYPE_CODE
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)

class TransbankController(http.Controller):
    _init_url = '/payment/transbank/init'
    _result_url = '/payment/transbank/result'
    _end_url = '/payment/transbank/end'
    _confirmation = '/shop/transbank/confirmation'
    _error = '/shop/transbank/cancelar'

    configuration = None
    webpay = None
    

    # Llamada a pagina init (Permite inicializar una transaccion en Webpay)
    @http.route([
        _init_url
    ], type='http', auth='none', methods=['POST'], csrf=False)
    def transbank_form_feedback(self, **post):
        order, transaction, base_url = self.check_param(post)
        if not transaction:
            return werkzeug.utils.redirect(urllib.parse.urljoin(base_url, self._error + '?type=f'))

        acquirer = transaction.acquirer_id
        cert_normal.certDictionary.setEnvironment(acquirer.environment)
        cert_normal.certDictionary.setCommerceCode(acquirer.commerce_id)

        # Esto debe estar en dos enpoint: init y return
        certificate = cert_normal.certDictionary.dictionaryCert()
        configuration = Configuration()
        configuration.setEnvironment(certificate['environment'])
        configuration.setCommerceCode(certificate['commerce_code'])
        configuration.setPrivateKey(certificate['private_key'])
        configuration.setPublicCert(certificate['public_cert'])
        configuration.setWebpayCert(certificate['webpay_cert'])

        webpay = Webpay(configuration)

        #base_url = request.httprequest.url_root
        #base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        client = {}
        try :
            amount = post['AMOUNT'] # Monto de la Transaccion
            buyOrder = post['BUYORDER'] # Identificador de la Orden
            urlFinal = urllib.parse.urljoin(base_url, self._end_url) # URL Final
            sessionId = '' # (Opcional) definido por el cliente
            urlReturn = urllib.parse.urljoin(base_url, self._result_url) # URL Returno

            request_dict = dict()
            request_dict['amount'] = amount
            request_dict['buyOrder'] = buyOrder
            request_dict['sessionId'] = sessionId
            request_dict['urlFinal'] = urlFinal
            request_dict['urlReturn'] = urlReturn

            # Ejecucion de metodo initTransaction
            client = webpay.getNormalTransaction().initTransaction(amount, buyOrder, sessionId, urlReturn, urlFinal)

            if (client["token"] == None and client["token"] == ""):
                # Redireccionar a página de error
                _logger.warn("ERROR INIT: {}".format(str(client)))
                _logger.error(str(client))
                transaction.sudo().write({
                            
                            'state_message':transaction.state_message+'\n'+format(str(client)) if transaction.state_message else format(str(client)),
                            'state':'error'
                    })
                return werkzeug.utils.redirect(urllib.parse.urljoin(base_url, self._error + '?type=b'))

        except Exception as e:
            # Redireccionar a página de error
            _logger.warn("EXCEPTION INIT: {}".format(str(e)))
            _logger.error(str(e))
            transaction.sudo().write({
                      'acquirer_reference': post.get('token_ws'),
                      'state_message':transaction.state_message+'\n'+format(str(client)) if transaction.state_message else format(str(client)),
                      'state':'error'
                    })
            return werkzeug.utils.redirect(urllib.parse.urljoin(base_url, self._error + '?type=d'))
        
        transaction.sudo().write({'acquirer_reference': client["token"]})
        return werkzeug.utils.redirect(client['url']+'?token_ws='+client['token'])


    # Llamada a pagina result (Obtiene el detalle de la transacción)
    @http.route([
        _result_url
    ], type='http', auth='none', methods=['POST'], csrf=False)
    def transbank_result_feedback(self, **post):
        order, transaction, base_url = self.check_param(post)
        if not transaction:
            return werkzeug.utils.redirect(urllib.parse.urljoin(base_url, self._error + '?type=f'))

        acquirer = transaction.acquirer_id
        cert_normal.certDictionary.setEnvironment(acquirer.environment)
        cert_normal.certDictionary.setCommerceCode(acquirer.commerce_id)
        
        tbk_obj = request.env['payment.transbank']

        # Esto debe estar en cada endpoint
        certificate = cert_normal.certDictionary.dictionaryCert()
        configuration = Configuration()
        configuration.setEnvironment(certificate['environment'])
        configuration.setCommerceCode(certificate['commerce_code'])
        configuration.setPrivateKey(certificate['private_key'])
        configuration.setPublicCert(certificate['public_cert'])
        configuration.setWebpayCert(certificate['webpay_cert'])

        webpay = Webpay(configuration)

        client = {}
        if post.get('token_ws') is None :
            _logger.warn("ERROR RESULT: {}".format(str(post.get('token_ws'))))
            state_message = transaction.state_message+'\n'+format(str(client)) if transaction.state_message else format(str(client))
            transaction._set_transaction_error(state_message)
            transaction.write({'acquirer_reference': post.get('token_ws')})
            return werkzeug.utils.redirect(urllib.parse.urljoin(base_url, self._error + '?type=a'))

        elif post.get('token_ws') :
            client=False
            transaction_vals = {
                'acquirer_reference': post.get('token_ws')
            }

            # Ejecucion de metodo getTransaction
            try :
                token  = post.get('token_ws')

                request_dict = dict()
                request_dict['token'] = token
                _logger.warn("TOKEN: {}".format(str(token)))

                _logger.warn("REQUEST RESULT: {}".format(str(request_dict)))

                # Ejecución de método getTransaction
                _logger.warn("getNormalTransaction BEFORE")
                client = webpay.getNormalTransaction().getTransaction(token)
                _logger.warn("CLIENT: {}".format(str(client)))
                _logger.warn("TYPE detailOutput: {}".format(type(client.detailOutput)))
                if isinstance(client.detailOutput, list):
                    detailOutput = client.detailOutput[0]
                else:
                    detailOutput = client.detailOutput

                if detailOutput['responseCode'] == 0:
                    # si tiene cuotas
                    shares_amount = 0
                    if 'sharesAmount' in detailOutput:
                        shares_amount = detailOutput['sharesAmount']
                    transaction_vals.update({
                        'transbank_auth_transaction': detailOutput['authorizationCode'],
                        'transbank_payment_type': PAYMENT_TYPE_CODE[detailOutput['paymentTypeCode']],
                        'transbank_fee_type': detailOutput['sharesNumber'],
                        'transbank_amount_fee': shares_amount,
                        'transbank_last_digits': client.cardDetail.cardNumber,
                        'transbank_commerce_id': detailOutput['commerceCode'],
                    })

                    tbk_obj.sudo().create({
                        'order_id': order.id,
                        'buyorder': client.buyOrder,
                        'auth_transaction': detailOutput['authorizationCode'],
                        'payment_type': PAYMENT_TYPE_CODE[detailOutput['paymentTypeCode']],
                        'fee_type': detailOutput['sharesNumber'],
                        'amount_fee': shares_amount,
                        'last_digits': client.cardDetail.cardNumber,
                        'token_ws': token,
                    })
                    

                elif detailOutput['responseCode'] == -1:
                    _logger.warn("ERROR RESULT: {}".format(str(client)))
                    state_message = transaction.state_message+'\n'+format(str(client)) if transaction.state_message else format(str(client))
                    transaction._set_transaction_error(state_message)
                    transaction.write({'acquirer_reference': post.get('token_ws')})
                    return werkzeug.utils.redirect(urllib.parse.urljoin(base_url, self._error + '?type=a'))
                else:
                    _logger.warn("ERROR RESULT: {}".format(str(client)))
                    state_message = transaction.state_message+'\n'+format(str(client)) if transaction.state_message else format(str(client))
                    transaction._set_transaction_error(state_message)
                    transaction.write({'acquirer_reference': post.get('token_ws')})
                    return werkzeug.utils.redirect(urllib.parse.urljoin(base_url, self._error + '?type=e&code='+str(detailOutput['responseCode'])))

            except Exception as e:
                _logger.warn("EXCEPTION RESULT: {}".format(str(e)))
                _logger.error(str(e))
                state_message = transaction.state_message+'\n'+format(str(client)) if transaction.state_message else format(str(client))
                transaction._set_transaction_error(state_message)
                transaction.write({'acquirer_reference': post.get('token_ws')})
                return werkzeug.utils.redirect(urllib.parse.urljoin(base_url, self._error + '?type=f'))
            
            transaction.write(transaction_vals)
            sales_orders = transaction.mapped('sale_order_ids').filtered(lambda so: so.state == 'draft')
            sales_orders.with_context(tracking_disable=True).write({'state': 'sent'})
            transaction._set_transaction_authorized()
            values = {
                'urlRedirection': client['urlRedirection'],
                'token_ws': token,
            }
            return request.render('payment_transbank.webpay_redirect', values)

    @http.route([
        _end_url
    ], type='http', auth='none', methods=['POST'],csrf=False)
    def transbank_end_feedback(self, **post):
        order, transaction, base_url = self.check_param(post)
        if not transaction:
            return werkzeug.utils.redirect(urllib.parse.urljoin(base_url, self._error + '?type=f'))
        
        if post.get('TBK_TOKEN') or not post.get('token_ws'): #cuando anulan una transaccion no hay una variable token_ws sino una TBK_TOKEN. cosas de transbank
            transaction.sudo().write({
                            'state_message':transaction.state_message+'\n ERROR END:'+format(str(post)) if transaction.state_message else 'ERROR END: '+format(str(post)),
                            'state':'error'
                    })
            _logger.debug("ERROR END: {}".format(str(post)))
            return werkzeug.utils.redirect(urllib.parse.urljoin(base_url, self._error + f"?type=c&TBK_TOKEN={post.get('TBK_TOKEN')}"))
        
        _logger.debug("RESPONSE END: {}".format(str(post)))
        return werkzeug.utils.redirect(urllib.parse.urljoin(base_url, self._confirmation+'?token_ws='+post.get('token_ws')))
        
            

    @http.route([
        _confirmation
    ], type='http', auth="public", csrf=False, website=True)
    def payment_confirmation(self, **post):
        order, transaction, base_url = self.check_param(post)
        if not transaction:
            return werkzeug.utils.redirect(urllib.parse.urljoin(base_url, self._error + '?type=f'))
        if transaction:
            if transaction.state != 'done':
                transaction.sudo()._set_transaction_done()
            request.session['sale_order_id'] = None
            _logger.info(transaction.return_url)
            if order:
                return request.render("website_sale.confirmation", {'order' : order})
            else:
                return werkzeug.utils.redirect(urllib.parse.urljoin(base_url, transaction.return_url))

    @http.route([
        _error
    ], type='http', auth='public', csrf=False, website=True)
    def payment_error(self, **post):
        order, transaction, base_url = self.check_param(post)
        
        if post.get('type') == 'c':
            message = {
                'header': 'Vemos que has desistido de tu compra.',
                'body': 'Tal vez, estos no eran los productos que buscabas. Te invitamos a seguir mirando nuestro grandioso catálogo de productos',
                'detail': ''
            }
            if transaction:
                transaction.sudo().write({'state':'cancel'})
            
        elif post.get('type') == 'a':
            message = {
                'header': 'Oops!. La transacción no se ha podido terminar.',
                'body': 'Orden de compra ' + order.name,
                'detail':
                    '<p>Los posibles causas pueden ser:</p>'+
                    '<ul><li>Error en el ingreso de los datos de su tarjeta de Crédito o Débito (fecha y/o código de seguridad).</li>'+
                    '<li>Su tarjeta de Crédito o Débito no cuenta con saldo suficiente.</li>'+
                    '<li>Tarjeta aún no habilitada en el sistema financiero</li>'
            }


        elif post.get('type') == 'e':
            code = int(post.get('code'))
            code = code *-1
            message = {
                'header': 'Oops!. La transacción no se ha podido terminar.',
                'body': 'Orden de compra ' + order.name,
                'detail': RESPONSE_CODE[code]
                
            }

        elif post.get('type') == 'b' or post.get('type') == 'd' or post.get('type') == 'f':
            message = {
                'header': 'Lo sentimos mucho.',
                'body': 'Tenemos un inconveniente para realizar su compra. Solicitamos intentar nuevamente más tarde, gracias.',
                'detail': 'Solicitamos comunicarce con nosotros y reportar el problema, gracias.'
            }
        
        #order.sudo().write({'state':'cancel'})
        #request.session['sale_order_id'] = None
        return request.render('payment_transbank.error', { 'message': message })
    
    def check_param(self, post,**var):
        if post.get('token_ws'):
            transaction = request.env['payment.transaction'].sudo().search([('acquirer_reference','=',post.get('token_ws'))])
            order = transaction.sale_order_ids[0] if transaction.sale_order_ids else request.env['sale.order']
        elif post.get('TBK_TOKEN'):
            transaction = request.env['payment.transaction'].sudo().search([('acquirer_reference','=',post.get('TBK_TOKEN'))])
            order = transaction.sale_order_ids[0] if transaction.sale_order_ids else request.env['sale.order']
        elif post.get('transbank_order_id') and post.get('transbank_transaction_id'):
            order = request.env['sale.order'].sudo().browse(int(post.get('transbank_order_id')))
            transaction = request.env['payment.transaction'].sudo().browse(int(post.get('transbank_transaction_id')))
        elif post.get('BUYORDER'):
            transaction = request.env['payment.transaction'].sudo().search([('reference','=',post.get('BUYORDER'))])
            order = transaction.sale_order_ids[0] if transaction.sale_order_ids else request.env['sale.order']
        elif (request.session.get('sale_last_order_id') and request.session.get('__website_sale_last_tx_id')):
            order = request.env['sale.order'].sudo().browse(request.session.get('sale_last_order_id'))
            transaction = request.env['payment.transaction'].sudo().browse(request.session.get('__website_sale_last_tx_id'))
        else:
            order = False
            transaction = False
            _logger.warn("ERROR RESULT: no se pudo conseguir token, ultima orden o ultima transaccion")
        base_url = ""
        if transaction:
            if transaction.acquirer_id:
                base_url = transaction.acquirer_id.get_base_url()
        if not base_url and request:
            base_url = request.httprequest.url_root
        if not base_url:
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return order, transaction, base_url
            
