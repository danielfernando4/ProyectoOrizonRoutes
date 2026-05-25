import logging
from decimal import Decimal

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class PayPalClient:
    def __init__(self, client_id=None, client_secret=None, sandbox=True):
        self.client_id = client_id or settings.PAYPAL_CLIENT_ID
        self.client_secret = client_secret or settings.PAYPAL_CLIENT_SECRET
        self.sandbox = sandbox
        self.base_url = (
            "https://api-m.sandbox.paypal.com"
            if sandbox
            else "https://api-m.paypal.com"
        )
        self._access_token = None

    def _get_access_token(self):
        if self._access_token:
            return self._access_token

        response = requests.post(
            f"{self.base_url}/v1/oauth2/token",
            data={"grant_type": "client_credentials"},
            auth=(self.client_id, self.client_secret),
            headers={"Accept": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        logger.debug(f"PayPal OAuth token obtained successfully")
        self._access_token = data["access_token"]
        return self._access_token

    def _headers(self):
        return {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def create_order(self, value: Decimal, currency: str = "USD",
                     return_url: str = "", cancel_url: str = ""):
        try:
            payload = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "amount": {
                        "currency_code": currency,
                        "value": str(value),
                    },
                }],
                "application_context": {
                    "return_url": return_url,
                    "cancel_url": cancel_url,
                },
            }

            response = requests.post(
                f"{self.base_url}/v2/checkout/orders",
                json=payload,
                headers=self._headers(),
                timeout=30,
            )
            if not response.ok:
                logger.error(f"PayPal create_order failed: {response.status_code} {response.text}")
            response.raise_for_status()
            data = response.json()

            order_id = data["id"]
            approval_link = None
            for link in data.get("links", []):
                if link.get("rel") in ("approve", "payer-action"):
                    approval_link = link["href"]
                    break

            if not approval_link:
                approval_link = f"https://www.sandbox.paypal.com/checkoutnow?token={order_id}"

            return order_id, approval_link
        except requests.RequestException as e:
            logger.error(f"PayPal create_order error: {e}")
            raise

    def capture_order(self, order_id: str):
        try:
            response = requests.post(
                f"{self.base_url}/v2/checkout/orders/{order_id}/capture",
                headers=self._headers(),
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            capture_id = None
            status = data.get("status", "UNKNOWN")

            for pu in data.get("purchase_units", []):
                captures = pu.get("payments", {}).get("captures", [])
                if captures:
                    capture_id = captures[0]["id"]
                    status = captures[0].get("status", status)
                    break

            return capture_id, status
        except requests.RequestException as e:
            logger.error(f"PayPal capture_order error: {e}")
            raise

    def refund_capture(self, capture_id: str):
        try:
            response = requests.post(
                f"{self.base_url}/v2/payments/captures/{capture_id}/refund",
                json={},
                headers=self._headers(),
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("id"), data.get("status", "COMPLETED")
        except requests.RequestException as e:
            logger.error(f"PayPal refund error: {e}")
            raise


_paypal_client = None


def get_paypal_client():
    global _paypal_client
    if _paypal_client is None:
        _paypal_client = PayPalClient()
    return _paypal_client
