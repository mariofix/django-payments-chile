# django-payments-chile

`django-payments-chile` es una extensión para [django-payments](https://github.com/jazzband/django-payments), una biblioteca que proporciona una interfaz universal para procesar pagos en aplicaciones Django. Este proyecto añade soporte específico para varios proveedores de pagos chilenos como Flow, Khipu, Webpay, y otros.

:warning: :warning: **Este proyecto está en desarrollo activo**, usar con precaución. :warning: :warning:

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
| Flow | :white_check_mark: | Plataforma chilena para pagos en línea que admite múltiples métodos de pago. |
| Khipu | :white_check_mark: | Permite pagos mediante transferencia electrónica en tiempo real. |
| Klap | :x: | Solución de pagos electrónicos enfocados en comercios. |
| Kushki | :x: | Proveedor de pagos electrónicos que facilita la integración con diversas plataformas. |
| Payku | :x: | Plataforma de pagos enfocada en pequeñas y medianas empresas. |
| Webpay | :white_check_mark: | El sistema de pago en línea más utilizado en Chile, operado por Transbank. |

## Características

- Soporte para múltiples proveedores de pago en un solo proyecto.
- API consistente para crear, procesar y verificar transacciones.
- Fácil configuración y personalización.
- Documentación clara para desarrolladores.
- Soporte para eventos de éxito, fallo, y reembolsos de pagos.

## Instalación

```bash
pip install django-payments-chile
```

### Configuración de Proveedores

Agrega las credenciales de los proveedores de pago en tu archivo de configuración:

```python
PAYMENT_VARIANTS = {
    'flow': ('django_payments_chile.FlowProvider', {
        'api_key': 'tu_api_key_flow',
        'secret': 'tu_secret_flow',
    }),
    'webpay': ('django_payments_chile.WebpayProvider', {
        'commerce_code': 'tu_commerce_code_webpay',
        'api_key': 'tu_api_key_webpay',
    }),
}
```

## Licencia

Este proyecto no está afiliado, asociado ni patrocinado por ninguna de las empresas mencionadas en el listado de compatibilidad.

El código de este proyecto está disponible bajo la licencia [MIT](LICENSE), lo que significa que puedes utilizarlo, modificarlo y distribuirlo de manera libre, sujeto a las condiciones establecidas en dicha licencia.
