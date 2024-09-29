# django-payments-chile

![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)
![Django Version](https://img.shields.io/badge/django-3.2%2B-green)
![License](https://img.shields.io/badge/license-MIT-brightgreen)
![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen)

**django-payments-chile** es una librería diseñada para facilitar la integración de pagos en aplicaciones Django a través de múltiples proveedores en Chile. Este proyecto ofrece una API simple y flexible para procesar pagos de manera segura, permitiendo a los desarrolladores concentrarse en construir sus aplicaciones sin complicarse con la lógica de integración de cada proveedor.

## Proveedores de pago soportados

- **Flow**: Plataforma chilena para pagos en línea que admite múltiples métodos de pago.
- **Khipu**: Permite pagos mediante transferencia electrónica en tiempo real.
- **Klap**: Solución de pagos electrónicos enfocados en comercios.
- **Kushki**: Proveedor de pagos electrónicos que facilita la integración con diversas plataformas.
- **Payku**: Plataforma de pagos enfocada en pequeñas y medianas empresas.
- **Webpay**: El sistema de pago en línea más utilizado en Chile, operado por Transbank.
- **Onepay**: Pago rápido y seguro usando códigos QR.

## Características

- Soporte para múltiples proveedores de pago en un solo proyecto.
- API consistente para crear, procesar y verificar transacciones.
- Fácil configuración y personalización.
- Documentación clara para desarrolladores.
- Soporte para eventos de éxito, fallo, y reembolsos de pagos.

## Instalación

Para instalar la librería, utiliza pip:

```bash
pip install django-payments-chile
```

### Configuración de Proveedores

Agrega las credenciales de los proveedores de pago en tu archivo de configuración:

```python
PAYMENTS_PROVIDERS = {
    'FLOW': {
        'api_key': 'tu_api_key_flow',
        'secret': 'tu_secret_flow',
    },
    'KHIPU': {
        'receiver_id': 'tu_receiver_id',
        'secret': 'tu_secret_khipu',
    },
    'WEBPAY': {
        'commerce_code': 'tu_commerce_code_webpay',
        'api_key': 'tu_api_key_webpay',
    },
    ...
}
```

## Uso

Para crear y procesar un pago con **django-payments-chile**, simplemente importa el gateway y realiza la transacción:

```python
from payments_chile import PaymentGateway

gateway = PaymentGateway(provider='webpay')
response = gateway.create_payment(amount=10000, order_id='123456', return_url='https://tu-sitio.com/return/')
```

Luego, puedes verificar el estado del pago:

```python
if gateway.verify_payment(response):
    # Pago exitoso
else:
    # Pago fallido
```

## Proveedores adicionales

Puedes agregar más proveedores de pago mediante la extensión del gateway o contribuyendo con tus propias integraciones. Cada proveedor tiene una interfaz consistente para facilitar su uso y configuración.

## Contribuciones

Contribuciones son bienvenidas. Por favor, abre un [issue](https://github.com/mariofix/django-payments-chile/issues) o envía un pull request.

Pasos para contribuir:

1. Haz un fork del repositorio.
2. Crea una rama nueva para tu funcionalidad (`git checkout -b feature-nueva-funcionalidad`).
3. Realiza los cambios y asegúrate de probarlos.
4. Envía un pull request con una descripción clara de tu contribución.

## Licencia

Este proyecto está licenciado bajo la licencia [MIT](LICENSE).
