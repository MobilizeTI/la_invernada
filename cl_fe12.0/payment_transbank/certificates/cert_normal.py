"""
  @author     Allware Ltda. (http://www.allware.cl)
  @copyright  2015 Transbank S.A. (http://www.tranbank.cl)
  @date       Jan 2015
  @license    GNU LGPL
  @version    2.0.1
"""

import os

environment = 'INTEGRACION'
commerce_code = '597020000541'

class certDictionary():



    @staticmethod
    def dictionaryCert():
        global environment
        global commerce_code

        certificate = dict()
        dir = os.path.dirname(__file__)+'/integracion_normal/'
        if environment=='INTEGRACION':
            dir = dir + 'test/'
        
        
        
        """ ATENCION: Configurar modo de uso (INTEGRACION, CERTIFICACION o PRODUCCION) """
        certificate['environment'] = environment
        
        """ Llave Privada: Configura tu ruta absoluta """
        certificate['private_key'] = dir+commerce_code+'.key'
        
        """ Certificado Publico: Configura tu ruta absoluta """
        certificate['public_cert'] = dir+commerce_code+'.crt'
        
        """ Certificado Privado: Configura tu ruta absoluta """
        certificate['webpay_cert'] = dir + 'tbk.pem'
        
        """ Codigo Comercio """
        certificate['commerce_code'] = commerce_code
            
        return certificate

    @staticmethod
    def setEnvironment(envi):
        _envi = {'test':'INTEGRACION','cert':'CERTIFICACION','prod':'PRODUCCION'}
        global environment
        environment = _envi[envi]

    @staticmethod
    def setCommerceCode(commerceCode):
        global commerce_code
        print(commerceCode)
        commerce_code = commerceCode if commerceCode != False else '597020000541'
        print(commerce_code)