from OpenSSL import crypto

import os
import logging

_logger = logging.getLogger(__name__)


class TransbankCertificate(object):
    TYPE_RSA = crypto.TYPE_RSA

    def __ini__(self):
        self.certificate = ''

    def createKeys(self, type_, bits):
        pkey = crypto.PKey()
        pkey.generate_key(type_, bits)
        return pkey

    def createCert(self, pkey, **args):
        req = crypto.X509Req()
        subj = req.get_subject()

        for key, value in list(args.items()):
            setattr(subj, key, value)

        req.set_pubkey(pkey)
        req.sign(pkey, 'sha256')
        return req

    def signCert(self, cert, issuerCertKey, validityPeriod):
        issuerCert, issuerKey = issuerCertKey
        notBefore, notAfter = validityPeriod
        certSigned = crypto.X509()
        certSigned.set_serial_number(0)
        certSigned.gmtime_adj_notBefore(notBefore)
        certSigned.gmtime_adj_notAfter(notAfter)
        certSigned.set_issuer(issuerCert.get_subject())
        certSigned.set_subject(cert.get_subject())
        certSigned.set_pubkey(cert.get_pubkey())
        certSigned.sign(issuerKey, 'sha256')
        return certSigned

    def saveCert(self, pkey, signed_cert,name):
        path = os.path.dirname(os.path.dirname(__file__))

        with open(os.path.join(path, "certificates/integracion_normal", (name+".key")), 'w') as _pkey:
            _pkey.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey).decode('utf-8'))

        with open(os.path.join(path, "certificates/integracion_normal", (name + ".crt")), 'w') as ca:
            ca.write(crypto.dump_certificate(crypto.FILETYPE_PEM, signed_cert).decode('utf-8'))

        self.certificate = crypto.dump_certificate(crypto.FILETYPE_PEM, signed_cert).decode('utf-8')
        #crypto.dump_publickey(crypto.FILETYPE_PEM, pkey)

    def getPublicKey(self):
        return self.certificate
