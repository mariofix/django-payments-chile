from __future__ import annotations

from typing import Any

import requests
from django.http import JsonResponse
from payments import PaymentError, PaymentStatus, RedirectNeeded
from payments.core import BasicProvider
from payments.forms import PaymentForm as BasePaymentForm

vci_status = {
    "TSY": "Autenticación Exitosa",
    "TSN": "Autenticación Rechazada",
    "NP": "No Participa, sin autenticación",
    "U3": "Falla conexión, Autenticación Rechazada",
    "INV": "Datos Inválidos",
    "A": "Intentó",
    "CNP1": "Comercio no participa",
    "EOP": "Error operacional",
    "BNA": "BIN no adherido",
    "ENA": "Emisor no adherido",
    "TSYS": "Autenticación exitosa Sin fricción. Resultado autenticación: Autenticación Existosa",
    "TSAS": "Intento, tarjeta no enrolada / emisor no disponible. Resultado autenticación: Autenticación Exitosa",
    "TSNS": "Fallido, no autenticado, denegado / no permite intentos. Resultado autenticación: Autenticación denegada",
    "TSRS": "Autenticación rechazada - sin fricción. Resultado autenticación: Autenticación rechazada",
    "TSUS": "Autenticación no se pudo realizar por problema técnico u otro motivo. Resultado autenticación: \
        Autenticación fallida",
    "TSCF": "Autenticación con fricción(No aceptada por el comercio). Resultado autenticación: Autenticación \
        incompleta",
    "TSYF": "Autenticación exitosa con fricción. Resultado autenticación: Autenticación exitosa",
    "TSNF": "No autenticado. Transacción denegada con fricción. Resultado autenticación: Autenticación denegada",
    "TSUF": "Autenticación con fricción no se pudo realizar por problema técnico u otro. Resultado autenticación: \
        Autenticación fallida",
    "NPC": "Comercio no Participa. Resultado autenticación: Comercio/BIN no participa",
    "NPB": "BIN no participa. Resultado autenticación: Comercio/BIN no participa",
    "NPCB": "Comercio y BIN no participan. Resultado autenticación: Comercio/BIN no participa",
    "SPCB": "Comercio y BIN sí participan. Resultado autenticación: Autorización incompleta",
}

tipo_de_pagos = {
    "VD": "Venta Débito.",
    "VN": "Venta Normal.",
    "VC": "Venta en cuotas.",
    "SI": "3 cuotas sin interés.",
    "S2": "2 cuotas sin interés.",
    "NC": "N Cuotas sin interés",
    "VP": "Venta Prepago.",
}

codigos_rechazo_nivel_1 = {
    "-1": "Rechazo - Posible error en el ingreso de datos de la transacción",
    "-2": "Rechazo - Se produjo fallo al procesar la transacción, este mensaje de rechazo se encuentra relacionado \
        a parámetros de la tarjeta y/o su cuenta asociada",
    "-3": "Rechazo - Error en Transacción",
    "-4": "Rechazo - Rechazada por parte del emisor",
    "-5": "Rechazo - Transacción con riesgo de posible fraude",
}

codigo_rechazo_refund = {
    "304": "Validación de campos de entrada nulos",
    "245": "Código de comercio no existe",
    "22": "El comercio no se encuentra activo",
    "316": "El comercio indicado no corresponde al certificado o no es hijo del comercio MALL en caso de \
        transacciones MALL",
    "308": "Operación no permitida",
    "274": "Transacción no encontrada",
    "16": "La transacción no permite anulación",
    "292": "La transacción no está autorizada",
    "284": "Periodo de anulación excedido",
    "310": "Transacción anulada previamente",
    "311": "Monto a anular excede el saldo disponible para anular",
    "312": "Error genérico para anulaciones",
    "315": "Error del autorizador",
    "53": "La transacción no permite anulación parcial de transacciones con cuotas",
}


class WebpayProvider(BasicProvider):
    """
    WebpayProvider es una clase que proporciona integración con Transbank para procesar pagos.
    Inicializa una instancia de WebpayProvider con el key y el secreto de Transbank.

    Args:
        api_key_id (str): ApiKey entregada por Transbank.
        api_key_secret (str): ApiSecret entregada por Transbank.
        api_endpoint (str): Ambiente Transbank, puede ser "produccion" o "integracion" (Valor por defecto: produccion)
        **kwargs: Argumentos adicionales.
    """

    form_class = BasePaymentForm
    api_endpoint: str
    api_key_id: str = None
    api_key_secret: str = None

    def __init__(
        self,
        api_key_id: str,
        api_key_secret: str,
        api_endpoint: str = "produccion",
        **kwargs: int,
    ):
        super().__init__(**kwargs)
        self.api_endpoint = api_endpoint
        self.api_key_id = api_key_id
        self.api_key_secret = api_key_secret
        if self.api_endpoint == "produccion":
            self.api_endpoint = "https://webpay3g.transbank.cl/"
        elif self.api_endpoint == "integracion":
            self.api_endpoint = "https://webpay3gint.transbank.cl/"

    def get_form(self, payment, data: dict | None = None) -> Any:
        """
        Genera el formulario de pago para redirigir a la página de pago.

        Args:
            payment ("Payment"): Objeto de pago Django Payments.
            data (dict | None): Datos del formulario (opcional).

        Returns:
            Any: Formulario de pago redirigido a la página de pago.

        Raises:
            RedirectNeeded: Redirige a la página de pago.

        """
        if not payment.transaction_id:
            datos_para_tbk = {
                "buy_order": str(payment.token),
                "session": str(payment.token),
                "return_url": payment.get_process_url(),
                "amount": int(payment.total),
            }

            try:
                pago_req = requests.post(
                    f"{self.api_endpoint}/rswebpaytransaction/api/webpay/v1.2/transactions",
                    data=datos_para_tbk,
                    timeout=5,
                )
                pago_req.raise_for_status()

            except Exception as pe:
                payment.change_status(PaymentStatus.ERROR, str(pe))
                raise PaymentError(pe)
            else:
                pago = pago_req.json()
                payment.transaction_id = pago["token"]
                payment.extra_data["request_tbk"] = datos_para_tbk
                payment.extra_data["respuesta_tbk"] = pago
                payment.save()
                payment.change_status(PaymentStatus.PREAUTH)

            raise RedirectNeeded(f"{pago['url']}?token_ws={pago['token']}")

    def genera_headers(self):
        return {
            "Content-Type": "application/json",
            "Tbk-Api-Key-Id": self.api_key_id,
            "Tbk-Api-Key-Secret": self.api_key_secret,
        }

    def process_data(self, payment, request) -> JsonResponse:
        """
        Procesa la captura del pago
        Usuario deberia volver acá y luego a la pagina de muestra de informacion.

        Args:
            payment ("Payment"): Objeto de pago Django Payments.
            request ("HttpRequest"): Objeto de solicitud HTTP de Django.

        Returns:
            JsonResponse: Respuesta JSON que indica el procesamiento de los datos del pago.

        """

        if payment.status in [PaymentStatus.WAITING, PaymentStatus.PREAUTH]:
            self.commit(self.get_token_from_request(payment, request), payment)

        return JsonResponse({"status": "ok"})

    def get_token_from_request(self, payment, request) -> str:
        """Return payment token from provider request."""

        try:
            return request.POST["token_ws"] or request.GET["token_ws"]
        except Exception as e:
            raise PaymentError(
                code=400,
                message="token_ws is not present",
            ) from e

    def actualiza_estado(self, payment) -> dict:
        """Actualiza el estado del pago con Flow

        Args:
            payment ("Payment): Objeto de pago Django Payments.

        Returns:
            dict: Diccionario con valores del objeto `PaymentStatus`.
        """

        status_req = requests.put(
            f"{self.api_endpoint}/rswebpaytransaction/api/webpay/v1.2/transactions/{payment.token}",
            timeout=5,
            headers=self.genera_headers(),
        )
        status_req.raise_for_status()

        status = status_req.json()
        payment.extra_data["status_response"] = status
        payment.save()

        if status["response_code"] == 0:
            payment.change_status(PaymentStatus.CONFIRMED)
            return PaymentStatus.CONFIRMED
        payment.change_status(PaymentStatus.REJECTED)
        return PaymentStatus.REJECTED

    def commit(self, token, payment):
        """Se debe llamar al procesar el retorno"""
        commit_req = requests.put(
            f"{self.api_endpoint}/rswebpaytransaction/api/webpay/v1.2/transactions/{token}",
            timeout=5,
            headers=self.genera_headers(),
        )
        commit_req.raise_for_status()

        commit = commit_req.json()
        commit["vci_str"] = self.agrega_info_error("vci", commit["vci"])
        commit["payment_type_code_str"] = self.agrega_info_error("pago", commit["payment_type_code"])
        payment.extra_data["commit_response"] = commit
        payment.save()
        if commit["status"] == "AUTHORIZED" and commit["response_code"] == 0:
            raise RedirectNeeded("success")
        raise RedirectNeeded("error")

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

        refund_data = {"amount": amount or payment.total}
        refund_req = requests.put(
            f"{self.api_endpoint}/rswebpaytransaction/api/webpay/v1.2/transactions/{payment.token}/refunds",
            timeout=5,
            headers=self.genera_headers(),
            data=refund_data,
        )
        refund_req.raise_for_status()

        refund = refund_req.json()
        refund["response_code_str"] = self.agrega_info_error("refund", refund["response_code"])
        payment.extra_data["refund_response"] = refund
        payment.save()

        if refund["type"] == "REVERSED":
            payment.change_status(PaymentStatus.REFUNDED)
            return payment.total
        if refund["type"] == "NULLIFIED" and refund["response_code"] == 0:
            payment.change_status(PaymentStatus.REFUNDED)
            return refund["nullified_amount"]

    def agrega_info_error(self, tipo, codigo):
        if tipo == "vci":
            return vci_status.get(codigo)
        if tipo == "pago":
            return tipo_de_pagos.get(codigo)
        if tipo == "rechazo_l1":
            return codigos_rechazo_nivel_1.get(codigo)
        if tipo == "refund":
            return codigo_rechazo_refund.get(codigo)
        return None
