from __future__ import annotations

from unittest import TestCase
from unittest.mock import Mock, patch

import requests
from payments import PaymentError, PaymentStatus, RedirectNeeded

from django_payments_chile.KhipuProvider import KhipuProvider

API_KEY = "khipu_test_key"  # nosec
API_ENDPOINT = "https://payment-api.khipu.com"


class Payment(Mock):
    id = 1
    description = "payment"
    currency = "CLP"
    delivery = 0
    status = PaymentStatus.WAITING
    message = None
    tax = 0
    total = 5000
    captured_amount = 0
    transaction_id = None
    billing_email = "correo@usuario.com"
    extra_data = {}

    def change_status(self, status, message=""):
        self.status = status
        self.message = message

    def get_failure_url(self):
        return "https://mi-app.cl/error"

    def get_process_url(self):
        return "https://mi-app.cl/process"

    def get_purchased_items(self):
        return []

    def get_success_url(self):
        return "https://mi-app.cl/exito"


class TestKhipuProvider(TestCase):
    def test_provider_create_session_success(self):
        test_payment = Payment()
        test_payment.extra_data["datos_extra"] = {"payment_currency": "CLP", "currency": "CLP"}
        provider = KhipuProvider(api_key=API_KEY, api_endpoint=API_ENDPOINT)

        with patch("django_payments_chile.KhipuProvider.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "payment_id": "test_payment_id",
                "payment_url": "https://khipu.com/payment",
                "simplified_transfer_url": "https://app.khipu.com/payment/simplified",
                "transfer_url": "https://khipu.com/payment/manual",
                "app_url": "khipu:///pos/test",
                "ready_for_terminal": False,
            }
            mock_post.return_value = mock_response

            with self.assertRaises(RedirectNeeded):
                provider.get_form(test_payment)

            self.assertEqual(test_payment.status, PaymentStatus.WAITING)
            self.assertEqual(test_payment.extra_data["respuesta_khipu"]["payment_id"], "test_payment_id")
            self.assertEqual(
                test_payment.extra_data["respuesta_khipu"]["payment_url"],
                "https://khipu.com/payment",
            )

    def test_provider_create_session_failure(self):
        test_payment = Payment()
        provider = KhipuProvider(api_key=API_KEY, api_endpoint=API_ENDPOINT)

        with patch("django_payments_chile.KhipuProvider.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.exceptions.RequestException("Error")
            mock_post.return_value = mock_response

            with self.assertRaises(PaymentError):
                provider.get_form(test_payment)

            self.assertEqual(test_payment.status, PaymentStatus.ERROR)

    def test_process_data_success(self):
        test_payment = Payment()
        provider = KhipuProvider(api_key=API_KEY, api_endpoint=API_ENDPOINT)

        with patch("django_payments_chile.KhipuProvider.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "status": "done",
                "status_detail": "normal",
            }
            mock_get.return_value = mock_response

            provider.actualiza_estado(test_payment)

            self.assertEqual(test_payment.status, PaymentStatus.CONFIRMED)

    def test_refund_success(self):
        test_payment = Payment()
        test_payment.status = PaymentStatus.CONFIRMED
        provider = KhipuProvider(api_key=API_KEY, api_endpoint=API_ENDPOINT)

        with patch("django_payments_chile.KhipuProvider.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"message": "Refund created"}
            mock_post.return_value = mock_response

            refund_amount = provider.refund(test_payment, amount=3000)

            self.assertEqual(refund_amount, 3000)
            self.assertEqual(test_payment.status, PaymentStatus.REFUNDED)

    def test_refund_failure_unconfirmed(self):
        test_payment = Payment()
        test_payment.status = PaymentStatus.WAITING
        provider = KhipuProvider(api_key=API_KEY, api_endpoint=API_ENDPOINT)

        with self.assertRaises(PaymentError):
            provider.refund(test_payment, amount=3000)
