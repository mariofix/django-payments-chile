from __future__ import annotations

from unittest import TestCase
from unittest.mock import Mock, patch

import requests
from payments import PaymentError, PaymentStatus, RedirectNeeded

from django_payments_chile.WebpayProvider import WebpayProvider

API_KEY_ID = "tbk_test_key_id"  # nosec
API_KEY_SECRET = "tbk_test_key_secret"  # nosec


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
    token = "test-token-123"
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


class TestWebpayProvider(TestCase):
    def test_provider_produccion(self):
        provider = WebpayProvider(api_key_id=API_KEY_ID, api_key_secret=API_KEY_SECRET)
        self.assertEqual(provider.api_endpoint, "https://webpay3g.transbank.cl/")

    def test_provider_integracion(self):
        provider = WebpayProvider(
            api_key_id=API_KEY_ID,
            api_key_secret=API_KEY_SECRET,
            api_endpoint="integracion",
        )
        self.assertEqual(provider.api_endpoint, "https://webpay3gint.transbank.cl/")

    def test_get_form_success(self):
        test_payment = Payment()
        provider = WebpayProvider(api_key_id=API_KEY_ID, api_key_secret=API_KEY_SECRET)

        with patch("django_payments_chile.WebpayProvider.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "url": "https://webpay3g.transbank.cl/webpayserver/initTransaction",
                "token": "TBK_TOKEN_123",
            }
            mock_post.return_value = mock_response

            with self.assertRaises(RedirectNeeded):
                provider.get_form(test_payment)

            self.assertEqual(test_payment.status, PaymentStatus.PREAUTH)
            self.assertEqual(test_payment.transaction_id, "TBK_TOKEN_123")
            self.assertEqual(test_payment.extra_data["respuesta_tbk"]["token"], "TBK_TOKEN_123")

    def test_get_form_error(self):
        test_payment = Payment()
        provider = WebpayProvider(api_key_id=API_KEY_ID, api_key_secret=API_KEY_SECRET)

        with patch("django_payments_chile.WebpayProvider.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.exceptions.RequestException("Error occurred")
            mock_post.return_value = mock_response

            with self.assertRaises(PaymentError):
                provider.get_form(test_payment)

            self.assertEqual(test_payment.status, PaymentStatus.ERROR)

    def test_process_data_calls_commit(self):
        test_payment = Payment()
        test_payment.status = PaymentStatus.PREAUTH
        provider = WebpayProvider(api_key_id=API_KEY_ID, api_key_secret=API_KEY_SECRET)

        mock_request = Mock()
        mock_request.POST = {"token_ws": "TBK_TOKEN_123"}
        mock_request.GET = {}

        with patch.object(provider, "commit") as mock_commit:
            provider.process_data(test_payment, mock_request)
            mock_commit.assert_called_once_with("TBK_TOKEN_123", test_payment)

    def test_process_data_returns_json(self):
        test_payment = Payment()
        test_payment.status = PaymentStatus.CONFIRMED
        provider = WebpayProvider(api_key_id=API_KEY_ID, api_key_secret=API_KEY_SECRET)

        mock_request = Mock()
        response = provider.process_data(test_payment, mock_request)
        self.assertEqual(response.status_code, 200)

    def test_get_token_from_request_missing(self):
        provider = WebpayProvider(api_key_id=API_KEY_ID, api_key_secret=API_KEY_SECRET)
        mock_request = Mock()
        mock_request.POST = {}
        mock_request.GET = {}

        with self.assertRaises(PaymentError):
            provider.get_token_from_request(None, mock_request)

    def test_commit_authorized(self):
        test_payment = Payment()
        provider = WebpayProvider(api_key_id=API_KEY_ID, api_key_secret=API_KEY_SECRET)

        with patch("django_payments_chile.WebpayProvider.requests.put") as mock_put:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "status": "AUTHORIZED",
                "response_code": 0,
                "vci": "TSY",
                "payment_type_code": "VN",
            }
            mock_put.return_value = mock_response

            with self.assertRaises(RedirectNeeded) as ctx:
                provider.commit("TBK_TOKEN_123", test_payment)

            self.assertEqual(str(ctx.exception), "success")
            self.assertEqual(test_payment.extra_data["commit_response"]["vci_str"], "Autenticación Exitosa")

    def test_commit_rejected(self):
        test_payment = Payment()
        provider = WebpayProvider(api_key_id=API_KEY_ID, api_key_secret=API_KEY_SECRET)

        with patch("django_payments_chile.WebpayProvider.requests.put") as mock_put:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "status": "FAILED",
                "response_code": -1,
                "vci": "TSN",
                "payment_type_code": "VN",
            }
            mock_put.return_value = mock_response

            with self.assertRaises(RedirectNeeded) as ctx:
                provider.commit("TBK_TOKEN_123", test_payment)

            self.assertEqual(str(ctx.exception), "error")

    def test_actualiza_estado_confirmed(self):
        test_payment = Payment()
        provider = WebpayProvider(api_key_id=API_KEY_ID, api_key_secret=API_KEY_SECRET)

        with patch("django_payments_chile.WebpayProvider.requests.put") as mock_put:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"response_code": 0}
            mock_put.return_value = mock_response

            result = provider.actualiza_estado(test_payment)

            self.assertEqual(result, PaymentStatus.CONFIRMED)
            self.assertEqual(test_payment.status, PaymentStatus.CONFIRMED)

    def test_actualiza_estado_rejected(self):
        test_payment = Payment()
        provider = WebpayProvider(api_key_id=API_KEY_ID, api_key_secret=API_KEY_SECRET)

        with patch("django_payments_chile.WebpayProvider.requests.put") as mock_put:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"response_code": -1}
            mock_put.return_value = mock_response

            result = provider.actualiza_estado(test_payment)

            self.assertEqual(result, PaymentStatus.REJECTED)
            self.assertEqual(test_payment.status, PaymentStatus.REJECTED)

    def test_refund_reversed(self):
        test_payment = Payment()
        test_payment.status = PaymentStatus.CONFIRMED
        provider = WebpayProvider(api_key_id=API_KEY_ID, api_key_secret=API_KEY_SECRET)

        with patch("django_payments_chile.WebpayProvider.requests.put") as mock_put:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "type": "REVERSED",
                "response_code": 0,
            }
            mock_put.return_value = mock_response

            result = provider.refund(test_payment)

            self.assertEqual(result, test_payment.total)
            self.assertEqual(test_payment.status, PaymentStatus.REFUNDED)

    def test_refund_nullified(self):
        test_payment = Payment()
        test_payment.status = PaymentStatus.CONFIRMED
        provider = WebpayProvider(api_key_id=API_KEY_ID, api_key_secret=API_KEY_SECRET)

        with patch("django_payments_chile.WebpayProvider.requests.put") as mock_put:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "type": "NULLIFIED",
                "response_code": 0,
                "nullified_amount": 3000,
            }
            mock_put.return_value = mock_response

            result = provider.refund(test_payment, amount=3000)

            self.assertEqual(result, 3000)
            self.assertEqual(test_payment.status, PaymentStatus.REFUNDED)

    def test_refund_unconfirmed_raises(self):
        test_payment = Payment()
        test_payment.status = PaymentStatus.WAITING
        provider = WebpayProvider(api_key_id=API_KEY_ID, api_key_secret=API_KEY_SECRET)

        with self.assertRaises(PaymentError):
            provider.refund(test_payment)

    def test_agrega_info_error_vci(self):
        provider = WebpayProvider(api_key_id=API_KEY_ID, api_key_secret=API_KEY_SECRET)
        self.assertEqual(provider.agrega_info_error("vci", "TSY"), "Autenticación Exitosa")
        self.assertIsNone(provider.agrega_info_error("vci", "UNKNOWN"))

    def test_agrega_info_error_pago(self):
        provider = WebpayProvider(api_key_id=API_KEY_ID, api_key_secret=API_KEY_SECRET)
        self.assertEqual(provider.agrega_info_error("pago", "VN"), "Venta Normal.")

    def test_agrega_info_error_refund(self):
        provider = WebpayProvider(api_key_id=API_KEY_ID, api_key_secret=API_KEY_SECRET)
        result = provider.agrega_info_error("refund", "274")
        self.assertIsNotNone(result)
        self.assertIn("no encontrada", result)

    def test_agrega_info_error_unknown_tipo(self):
        provider = WebpayProvider(api_key_id=API_KEY_ID, api_key_secret=API_KEY_SECRET)
        self.assertIsNone(provider.agrega_info_error("unknown", "123"))
