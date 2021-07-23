from .configuration import Configuration
from .webpay_normal import WebpayNormal

class Webpay:

        def __init__(self, params):
            self.__configuration = params;
            return None;

        def getNormalTransaction(self):
            webpayNormal = WebpayNormal(self.__configuration);
            return webpayNormal