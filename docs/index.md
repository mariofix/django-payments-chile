# django-payments-chile

`django-payments-chile` es una extensión para [django-payments](https://github.com/jazzband/django-payments), una biblioteca que proporciona una interfaz universal para procesar pagos en aplicaciones Django. Este proyecto añade soporte específico para varios proveedores de pagos chilenos como Flow, Khipu, Webpay, y otros.

⚠️ ⚠️ **Este proyecto está en desarrollo activo**, usar con precaución. ⚠️ ⚠️

![PyPI - Status](https://img.shields.io/pypi/status/django-payments-chile)
[![Downloads](https://pepy.tech/badge/django-payments-chile)](https://pepy.tech/project/django-payments-chile)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/fde07768d1714b0b93c6addd5e13bb7f)](https://app.codacy.com/gh/mariofix/django-payments-chile/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![Codacy Badge](https://app.codacy.com/project/badge/Coverage/fde07768d1714b0b93c6addd5e13bb7f)](https://app.codacy.com/gh/mariofix/django-payments-chile/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_coverage)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/mariofix/django-payments-chile/main.svg)](https://results.pre-commit.ci/latest/github/mariofix/django-payments-chile/main)
[![Tests & Coverage](https://github.com/mariofix/django-payments-chile/actions/workflows/tests_coverage.yml/badge.svg?branch=main)](https://github.com/mariofix/django-payments-chile/actions/workflows/tests_coverage.yml)
![PyPI](https://img.shields.io/pypi/v/django-payments-chile)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-payments-chile)
![PyPI - Implementation](https://img.shields.io/pypi/implementation/django-payments-chile)
![PyPI - License](https://img.shields.io/pypi/l/django-payments-chile)

## Proveedores de pago soportados

| Proveedor | Estado | Descripcion |
| --- | --- | --- |
| Flow | ✅ | Plataforma chilena para pagos en línea que admite múltiples métodos de pago. |
| Khipu | ✅ | Permite pagos mediante transferencia electrónica en tiempo real. |
| Klap | ❌ | Solución de pagos electrónicos enfocados en comercios. |
| Kushki | ❌ | Proveedor de pagos electrónicos que facilita la integración con diversas plataformas. |
| Payku | ❌ | Plataforma de pagos enfocada en pequeñas y medianas empresas. |
| Webpay | ✅ | El sistema de pago en línea más utilizado en Chile, operado por Transbank. |

## Inicio rápido

## Instalación

La biblioteca `django-payments-chile` está disponible en PyPi.

```bash
pip install django-payments-chile
```

### Configuración

En tu archivo `settings.py`, configura los proveedores de pago que vas a utilizar:

```python
PAYMENT_VARIANTS = {
    'flow': ('payments_chile.flow.FlowProvider', {
        'api_key': 'tu_api_key_flow',
        'secret': 'tu_secret_flow',
    }),
    'webpay': ('payments_chile.webpay.WebpayProvider', {
        'commerce_code': 'tu_commerce_code_webpay',
        'api_key': 'tu_api_key_webpay',
    }),
    # Otros proveedores como khipu, klap, etc.
}
```

### Creación de un nuevo pago

Con django-payments ya configurado, puedes crear un nuevo pago utilizando los métodos nativos de la librería:

```python
from payments import get_payment_model

Payment = get_payment_model()

payment = Payment.objects.create(
    variant='flow',  # o 'webpay', 'khipu', debe coincidir con el indice en PAYMENT_VARIANTS
    description="Pago por Orden #123",
    total=10000,
    currency='CLP',
    billing_first_name='Juan',
    billing_last_name='Pérez',
    billing_email='juan.perez@example.com',
)

# Redirige al usuario al proveedor de pagos
redirect_url = payment.get_process_url()
return redirect(redirect_url)
```

Para más detalles sobre el flujo de pago y las respuestas de los proveedores, consulta la sección [configuración](configuration.md).
