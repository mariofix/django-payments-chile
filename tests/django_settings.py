from __future__ import annotations

import os

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "tienda_pruebas"))
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(PROJECT_ROOT, "templates")],
    }
]
USE_TZ = True
SECRET_KEY = "NOTREALLY"  # nosec
PAYMENT_HOST = "example.com"

INSTALLED_APPS = ["payments", "django.contrib.sites"]
