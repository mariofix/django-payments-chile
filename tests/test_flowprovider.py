from __future__ import annotations

from unittest import TestCase
from unittest.mock import Mock, patch

import requests
from payments import PaymentError, PaymentStatus, RedirectNeeded

from django_payments_chile.FlowProvider import FlowProvider

API_KEY = "flow_test_key"  # nosec
API_SECRET = "flow_test_secret"  # nosec


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
        return "http://mi-app.cl/error"

    def get_process_url(self):
        return "http://mi-app.cl/process"

    def get_purchased_items(self):
        return []

    def get_success_url(self):
        return "http://mi-app.cl/exito"


class TestFlowProvider(TestCase):
    def test_provider_create_session_success(self):
        test_payment = Payment()
        test_payment.extra_data["datos_extra"] = {"payment_currency": "CLP", "currency": "CLP"}
        provider = FlowProvider(api_key=API_KEY, api_secret=API_SECRET)
        with patch("django_payments_chile.FlowProvider.requests.post") as mock_post:
            # Configure mock response
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None  # Simulates no exception raised
            mock_response.json.return_value = {
                "url": "https://flow.cl",
                "token": "TOKEN_ID",
                "flowOrder": "ORDER_ID",
            }
            mock_post.return_value = mock_response

            with self.assertRaises(RedirectNeeded):
                provider.get_form(test_payment)

            self.assertEqual(test_payment.status, PaymentStatus.WAITING)
            self.assertEqual(test_payment.extra_data["respuesta_flow"]["url"], "https://flow.cl")
            self.assertEqual(test_payment.extra_data["respuesta_flow"]["token"], "TOKEN_ID")
            self.assertEqual(test_payment.extra_data["respuesta_flow"]["flowOrder"], "ORDER_ID")

    def test_provider_create_session_error(self):
        payment = Payment()
        provider = FlowProvider(api_key=API_KEY, api_secret=API_SECRET)
        with patch("django_payments_chile.FlowProvider.requests.post") as mock_post:
            # Simulate an error response
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.exceptions.RequestException("Error occurred")
            mock_post.return_value = mock_response

            with self.assertRaises(PaymentError):
                provider.get_form(payment)

            self.assertEqual(payment.status, PaymentStatus.ERROR)
            self.assertIn("Error occurred", payment.message)

    def test_provider_change_status(self):
        payment = Payment()
        payment.change_status(PaymentStatus.CONFIRMED, "Payment successful")

        self.assertEqual(payment.status, PaymentStatus.CONFIRMED)
        self.assertEqual(payment.message, "Payment successful")

    def test_provider_transaction_id_set(self):
        payment = Payment()
        provider = FlowProvider(api_key=API_KEY, api_secret=API_SECRET)
        with patch("django_payments_chile.FlowProvider.requests.post") as mock_post:
            # Configure mock response with transaction ID
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "url": "https://flow.cl",
                "token": "TOKEN_ID",
                "flowOrder": "ORDER_ID",
            }
            mock_post.return_value = mock_response

            with self.assertRaises(RedirectNeeded):
                provider.get_form(payment)

            self.assertEqual(payment.transaction_id, "TOKEN_ID")

    def test_provider_sandbox(self):
        provider = FlowProvider(api_key=API_KEY, api_secret=API_SECRET, api_endpoint="sandbox")

        self.assertEqual(provider.api_endpoint, "https://sandbox.flow.cl/api")

    def test_provider_refund_error(self):
        payment = Payment()
        provider = FlowProvider(api_key=API_KEY, api_secret=API_SECRET)
        with self.assertRaises(PaymentError):
            provider.refund(payment)

    def test_provider_full_refund(self):
        payment = Payment(status=PaymentStatus.CONFIRMED)
        provider = FlowProvider(api_key=API_KEY, api_secret=API_SECRET)
        with patch("django_payments_chile.FlowProvider.requests.post") as mock_post_refund:
            # Configure mock response
            mock_response_refund = Mock()
            mock_response_refund.raise_for_status.return_value = None  # Simulates no exception raised
            mock_response_refund.json.return_value = {
                "token": "C93B4FAD6D63ED9A3F25D21E5D6DD0105FA8CAAQ",
                "flowRefundOrder": "122767",
                "date": "2017-07-21 12:33:15",
                "status": "created",
                "amount": "12000.00",
                "fee": "240.00",
            }
            mock_post_refund.return_value = mock_response_refund

            refund = provider.refund(payment)
            # print(f"{refund = }")
            self.assertEqual(refund, payment.total)

    def test_provider_full_refund_error(self):
        payment = Payment(status=PaymentStatus.CONFIRMED)
        provider = FlowProvider(api_key=API_KEY, api_secret=API_SECRET)
        with patch("django_payments_chile.FlowProvider.requests.post") as mock_post:
            # Configure mock response
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.exceptions.RequestException("Error occurred")
            mock_post.return_value = mock_response

            with self.assertRaises(PaymentError):
                provider.get_form(payment)

    def test_provider_update_status_confirmed(self):
        test_payment = Payment()
        provider = FlowProvider(api_key=API_KEY, api_secret=API_SECRET)
        with patch("django_payments_chile.FlowProvider.requests.get") as mock_status:
            # Configure mock response
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None  # Simulates no exception raised
            mock_response.json.return_value = {
                "status": 2,
            }
            mock_status.return_value = mock_response

            provider.actualiza_estado(test_payment)

            self.assertEqual(test_payment.status, PaymentStatus.CONFIRMED)

    def test_provider_update_status_rejected(self):
        test_payment = Payment()
        provider = FlowProvider(api_key=API_KEY, api_secret=API_SECRET)
        with patch("django_payments_chile.FlowProvider.requests.get") as mock_status:
            # Configure mock response
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None  # Simulates no exception raised
            mock_response.json.return_value = {
                "status": 3,
            }
            mock_status.return_value = mock_response

            provider.actualiza_estado(test_payment)

            self.assertEqual(test_payment.status, PaymentStatus.REJECTED)

    def test_provider_update_status_error(self):
        test_payment = Payment()
        provider = FlowProvider(api_key=API_KEY, api_secret=API_SECRET)
        with patch("django_payments_chile.FlowProvider.requests.get") as mock_status:
            # Configure mock response
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None  # Simulates no exception raised
            mock_response.json.return_value = {
                "status": 4,
            }
            mock_status.return_value = mock_response

            provider.actualiza_estado(test_payment)

            self.assertEqual(test_payment.status, PaymentStatus.ERROR)
