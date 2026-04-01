from __future__ import annotations

from typing import Any

import requests
from django.http import HttpResponseBadRequest, JsonResponse
from payments import PaymentError, PaymentStatus, RedirectNeeded
from payments.core import BasicProvider
from payments.forms import PaymentForm as BasePaymentForm

from .clientes import ClienteAPI


class FlowProvider(BasicProvider):
    """
    FlowProvider es una clase que proporciona integración con Flow para procesar pagos.
    Inicializa una instancia de FlowProvider con el key y el secreto de Flow.

    Args:
        api_key (str): ApiKey entregada por Flow.
        api_secret (str): ApiSecret entregada por Flow.
        api_medio (int | None): Versión de la API de notificaciones a utilizar (Valor por defecto: 9).
        api_endpoint (str): Ambiente flow, puede ser "live" o "sandbox" (Valor por defecto: live).
        **kwargs: Argumentos adicionales.
    """

    form_class = BasePaymentForm
    api_endpoint: str
    api_key: str = None
    api_secret: str = None
    api_medio: int

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        api_endpoint: str = "live",
        api_medio: int = 9,
        **kwargs: int,
    ):
        super().__init__(**kwargs)
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_medio = api_medio
        if self.api_endpoint == "live":
            self.api_endpoint = "https://www.flow.cl/api"
        elif self.api_endpoint == "sandbox":
            self.api_endpoint = "https://sandbox.flow.cl/api"

    def get_form(self, payment, data: dict | None = None) -> Any:
        """
        Genera el formulario de pago para redirigir a la página de pago de Flow.

        Args:
            payment ("Payment"): Objeto de pago Django Payments.
            data (dict | None): Datos del formulario (opcional).

        Returns:
            Any: Formulario de pago redirigido a la página de pago de Flow.

        Raises:
            RedirectNeeded: Redirige a la página de pago de Flow.

        """
        if not payment.transaction_id:
            datos_para_flow = {
                "apiKey": self.api_key,
                "commerceOrder": str(payment.token),
                "urlReturn": payment.get_success_url(),
                "urlConfirmation": payment.get_process_url(),
                "subject": payment.description,
                "amount": int(payment.total),
                "paymentMethod": self.api_medio,
                "currency": payment.currency,
            }

            if payment.billing_email:
                datos_para_flow.update({"email": payment.billing_email})

            datos_para_flow.update(**self._extra_data(payment.extra_data))

            try:
                payment.extra_data["datos_payment_create_flow"] = datos_para_flow
                payment.save()
            except Exception as e:
                # Dificil llegar acá, y si llegamos es problema de django-payments
                raise PaymentError(f"Ocurrió un error al guardar attrs.datos_flow: {e}")  # noqa
            datos_para_flow = dict(sorted(datos_para_flow.items()))
            firma_datos = ClienteAPI.genera_firma(datos_para_flow, self.api_secret)
            datos_para_flow.update({"s": firma_datos})

            try:
                pago_req = requests.post(
                    f"{self.api_endpoint}/payment/create",
                    data=datos_para_flow,
                    timeout=5,
                )
                pago_req.raise_for_status()

            except Exception as pe:
                payment.change_status(PaymentStatus.ERROR, str(pe))
                raise PaymentError(pe)
            else:
                pago = pago_req.json()
                payment.transaction_id = pago["token"]
                payment.extra_data["respuesta_flow"] = {
                    "url": pago["url"],
                    "token": pago["token"],
                    "flowOrder": pago["flowOrder"],
                }
                payment.save()
                payment.change_status(PaymentStatus.WAITING)

            raise RedirectNeeded(f"{pago['url']}?token={pago['token']}")

    def process_data(self, payment, request) -> JsonResponse:
        """
        Procesa los datos del pago recibidos desde Flow.

        Args:
            payment ("Payment"): Objeto de pago Django Payments.
            request ("HttpRequest"): Objeto de solicitud HTTP de Django.

        Returns:
            JsonResponse: Respuesta JSON que indica el procesamiento de los datos del pago.

        """
        if "token" not in request.POST:
            return HttpResponseBadRequest("token no está en post")

        if payment.status in [PaymentStatus.WAITING, PaymentStatus.PREAUTH]:
            self.actualiza_estado(payment=payment)

        return JsonResponse({"status": "ok"})

    def actualiza_estado(self, payment) -> dict:
        """Actualiza el estado del pago con Flow

        Args:
            payment ("Payment): Objeto de pago Django Payments.

        Returns:
            dict: Diccionario con valores del objeto `PaymentStatus`.
        """
        datos_para_flow = {"apiKey": self.api_key, "token": payment.token}
        datos_para_flow = dict(sorted(datos_para_flow.items()))
        firma_datos = ClienteAPI.genera_firma(datos_para_flow, self.api_secret)
        datos_para_flow.update({"s": firma_datos})

        estado_req = requests.get(f"{self.api_endpoint}/payment/getStatus", data=datos_para_flow, timeout=5)
        estado_req.raise_for_status()

        status = estado_req.json()
        if status["status"] == 2:
            payment.change_status(PaymentStatus.CONFIRMED)
        elif status["status"] == 3:
            payment.change_status(PaymentStatus.REJECTED)
        elif status["status"] == 4:
            payment.change_status(PaymentStatus.ERROR)
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
            "commerceOrder",
            "urlReturn",
            "urlConfirmation",
            "amount",
            "subject",
            "paymentMethod",
            "currency",
        ]
        for valor in prohibidos:
            if valor in data:
                del data[valor]

        return data

    def refund(self, payment, amount: int | None = None) -> int:
        """
        Realiza un reembolso del pago.
        El seguimiendo se debe hacer directamente en Flow

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

        datos_reembolso = {
            "apiKey": self.api_key,
            "refundCommerceOrder": payment.token,
            "receiverEmail": payment.billing_email,
            "amount": to_refund,
            "urlCallBack": payment.get_process_url(),
            "commerceTrxId": payment.token,
            "flowTrxId": payment.extra_data["respuesta_flow"]["flowOrder"],
        }
        try:
            refun_req = requests.post(f"{self.api_endpoint}/refund/create", data=datos_reembolso, timeout=5)
            refun_req.raise_for_status()
        except Exception as pe:
            raise PaymentError(pe)
        else:
            payment.extra_data["solicitud_reembolso"] = refun_req.json()
            payment.save()
            payment.change_status(PaymentStatus.REFUNDED)
            return to_refund
