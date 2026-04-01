from __future__ import annotations

from decimal import Decimal
from typing import Any

import requests
from django.http import HttpResponseBadRequest, JsonResponse
from payments import PaymentError, PaymentStatus, RedirectNeeded
from payments.core import BasicProvider
from payments.forms import PaymentForm as BasePaymentForm


class KhipuProvider(BasicProvider):
    """
    KhipuProvider es una clase que proporciona integración con Khipu para procesar pagos.
    Inicializa una instancia de KhipuProvider con la nueva llave de api introducida en v3

    Args:
        api_key (str): ApiKey entregada por Khipu.
        **kwargs: Argumentos adicionales.
    """

    form_class = BasePaymentForm
    api_endpoint: str = "https://payment-api.khipu.com"
    api_key: str = None

    def __init__(
        self,
        api_key: str,
        api_endpoint: str,
        **kwargs: int,
    ):
        super().__init__(**kwargs)
        self.api_endpoint = api_endpoint
        self.api_key = api_key

    def get_form(self, payment, data: dict | None = None) -> Any:
        """
        Genera el formulario de pago para redirigir a la página de pago de Khipu.

        Args:
            payment ("Payment"): Objeto de pago Django Payments.
            data (dict | None): Datos del formulario (opcional).

        Returns:
            Any: Formulario de pago redirigido a la página de pago de Khipu.

        Raises:
            RedirectNeeded: Redirige a la página de pago de Khipu.

        """
        if not payment.transaction_id:
            datos_para_khipu = {
                "transaction_id": str(payment.token),
                "return_url": payment.get_success_url(),
                "notify_url": payment.get_process_url(),
                "subject": payment.description,
                "amount": Decimal(payment.total),
                "currency": payment.currency,
            }

            if payment.billing_email:
                datos_para_khipu.update({"payer_email": payment.billing_email})

            datos_para_khipu.update(**self._extra_data(payment.extra_data))

            payment.extra_data["datos_payment_create"] = datos_para_khipu
            payment.save()

            try:
                pago_req = requests.post(
                    f"{self.api_endpoint}/v3/payments",
                    data=datos_para_khipu,
                    timeout=5,
                    headers=self.genera_headers(),
                )
                pago_req.raise_for_status()

            except Exception as pe:
                payment.change_status(PaymentStatus.ERROR, str(pe))
                raise PaymentError(pe)
            else:
                pago = pago_req.json()
                payment.transaction_id = pago["payment_id"]
                payment.extra_data["respuesta_khipu"] = {
                    "payment_id": pago["payment_id"],
                    "payment_url": pago["payment_url"],
                    "simplified_transfer_url": pago["simplified_transfer_url"],
                    "transfer_url": pago["transfer_url"],
                    "app_url": pago["app_url"],
                    "ready_for_terminal": pago["ready_for_terminal"],
                }
                payment.save()
                payment.change_status(PaymentStatus.WAITING)

            raise RedirectNeeded(f"{pago['payment_url']}")

    def genera_headers(self):
        return {"Content-Type": "application/json", "x-api-key": self.api_key}

    def process_data(self, payment, request) -> JsonResponse:
        """
        Procesa los datos del pago recibidos desde Khipu.

        Args:
            payment ("Payment"): Objeto de pago Django Payments.
            request ("HttpRequest"): Objeto de solicitud HTTP de Django.

        Returns:
            JsonResponse: Respuesta JSON que indica el procesamiento de los datos del pago.

        """
        if "transaction_id" not in request.POST:
            return HttpResponseBadRequest("transaction_id no está en post")

        if payment.status in [PaymentStatus.WAITING, PaymentStatus.PREAUTH]:
            self.actualiza_estado(payment=payment)

        return JsonResponse({"status": "ok"})

    def actualiza_estado(self, payment) -> dict:
        """Actualiza el estado del pago con Khipu

        Args:
            payment ("Payment): Objeto de pago Django Payments.

        Returns:
            dict: Diccionario con valores del objeto `PaymentStatus`.
        """
        estado_req = requests.get(
            f"{self.api_endpoint}/v3/payments/{payment.token}",
            timeout=5,
            headers=self.genera_headers(),
        )
        estado_req.raise_for_status()

        status = estado_req.json()
        if status["status"] == "done" and status["status_detail"] == "normal":
            payment.change_status(PaymentStatus.CONFIRMED)
        elif status["status_detail"] in [
            "rejected-by-payer",
            "reversed",
            "marked-as-abuse",
        ]:
            payment.change_status(PaymentStatus.REJECTED)
        return status

    def _extra_data(self, extra_data) -> dict:
        """Busca los datos que son enviandos por django-payments y los saca del diccionario

        Args:
            extra_data (dict): Obtenido desde PaymentModel.extra_data

        Returns:
            dict: Diccionario con valores permitidos.
        """
        data = extra_data.get("datos_extra", {})
        if not data:
            return {}

        prohibidos = [
            "amount",
            "subject",
            "currency",
        ]
        for valor in prohibidos:
            if valor in data:
                del data[valor]

        return data

    def refund(self, payment, amount: int | None = None) -> int:
        """
        Realiza un reembolso del pago.
        El seguimiendo se debe hacer directamente en Khipu

        Args:
            payment ("Payment"): Objeto de pago Django Payments.
            amount (int | None): Monto a reembolsar (opcional).

        Returns:
            int: Monto de reembolso solicitado.

        Raises:
            PaymentError: Error al crear el reembolso.

        """
        if payment.status != PaymentStatus.CONFIRMED:
            raise PaymentError("El pago debe estar confirmado para reversarse.")

        to_refund = amount or payment.total

        datos_reembolso = {"amount": to_refund}
        try:
            refun_req = requests.post(
                f"{self.api_endpoint}/v3/payments/{payment.token}/refunds",
                data=datos_reembolso,
                timeout=5,
                headers=self.genera_headers(),
            )
            refun_req.raise_for_status()
        except Exception as pe:
            raise PaymentError(pe)
        else:
            payment.extra_data["solicitud_reembolso"] = refun_req.json()
            payment.save()
            payment.change_status(PaymentStatus.REFUNDED)
            return to_refund
