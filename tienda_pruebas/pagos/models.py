from __future__ import annotations

from django.conf import settings
from payments.models import BasePayment


class Pago(BasePayment):
    def get_failure_url(self) -> str:
        # Redirige a esta URL si el pago falla
        return f"https://{settings.PAYMENT_HOST}/payments/{self.pk}/failure"

    def get_success_url(self) -> str:
        # Redirige a esta URL si el pago es exitoso
        return f"https://{settings.PAYMENT_HOST}/payments/{self.pk}/success"
