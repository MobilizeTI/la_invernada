PAYMENT_TYPE_CODE = {
    'VD': 'Venta Débito',
    'VN': 'Venta Normal',
    'VC': 'Venta en cuotas',
    'SI': '3 cuotas sin interés',
    'S2': '2 cuotas sin interés',
    'NC': 'N Cuotas sin interés',
    'VP': 'Venta Prepago',
}

RESPONSE_CODE = {
    0: 'Transacción aprobada',
    1: 'Rechazo de transacción',
    2: 'Transacción debe reintentarse',
    3: 'Error de transacción',
    4: 'Rechazo de transacción',
    5: 'Rechazo por error de tasa',
    6: 'Excede cupo máximo mensual',
    7: 'Excede límite diario por transacción',
    8: 'Rubro no autorizado'
}

VCI = {
    "TSY": "Autenticación exitosa",
    "TSN": "Autenticación fallida.",
    "TO6": "Tiempo máximo excedido para autenticación.",
    "ABO": "Autenticación abortada por tarjetahabiente.",
    "U3": "Error interno en la autenticación."
}