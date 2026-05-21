import logging
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

import httpx

logger = logging.getLogger("webhooks.integrations")


@dataclass
class IntegrationConfig:
    name: str
    provider: str
    base_url: str
    auth_type: str  # api_key, oauth2, basic, bearer
    credentials: dict = field(default_factory=dict)
    headers: dict = field(default_factory=dict)
    is_active: bool = True
    metadata: dict = field(default_factory=dict)


class BaseIntegration:
    """Base class for third-party integrations."""

    def __init__(self, config: IntegrationConfig):
        self.config = config
        self._http: Optional[httpx.AsyncClient] = None

    @property
    def http(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            headers = {"Content-Type": "application/json", **self.config.headers}

            if self.config.auth_type == "api_key":
                key_header = self.config.credentials.get("header", "X-API-Key")
                headers[key_header] = self.config.credentials.get("key", "")
            elif self.config.auth_type == "bearer":
                headers["Authorization"] = f"Bearer {self.config.credentials.get('token', '')}"
            elif self.config.auth_type == "basic":
                import base64
                creds = base64.b64encode(
                    f"{self.config.credentials.get('username', '')}:{self.config.credentials.get('password', '')}".encode()
                ).decode()
                headers["Authorization"] = f"Basic {creds}"

            self._http = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers=headers,
                timeout=30,
            )
        return self._http

    async def health_check(self) -> dict:
        """Check if the integration endpoint is reachable."""
        try:
            resp = await self.http.get("/")
            return {"status": "ok", "status_code": resp.status_code}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def close(self):
        if self._http and not self._http.is_closed:
            await self._http.aclose()


class SlackIntegration(BaseIntegration):
    """Slack webhook integration for notifications."""

    async def send_message(self, channel: str, text: str, blocks: Optional[list] = None) -> dict:
        payload = {"channel": channel, "text": text}
        if blocks:
            payload["blocks"] = blocks

        try:
            resp = await self.http.post("/api/chat.postMessage", json=payload)
            resp.raise_for_status()
            return {"success": True, "data": resp.json()}
        except Exception as e:
            logger.error("Slack message failed: %s", str(e))
            return {"success": False, "error": str(e)}

    async def send_webhook(self, webhook_url: str, text: str, attachments: Optional[list] = None) -> dict:
        payload = {"text": text}
        if attachments:
            payload["attachments"] = attachments

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(webhook_url, json=payload)
                return {"success": resp.status_code == 200}
        except Exception as e:
            return {"success": False, "error": str(e)}


class EmailIntegration(BaseIntegration):
    """Email service integration (SendGrid, Mailgun, etc.)."""

    async def send_email(
        self,
        to: str,
        subject: str,
        body_html: str,
        from_email: Optional[str] = None,
    ) -> dict:
        provider = self.config.metadata.get("provider", "sendgrid")

        if provider == "sendgrid":
            return await self._send_sendgrid(to, subject, body_html, from_email)
        elif provider == "mailgun":
            return await self._send_mailgun(to, subject, body_html, from_email)
        else:
            return {"success": False, "error": f"Unknown email provider: {provider}"}

    async def _send_sendgrid(self, to: str, subject: str, body_html: str, from_email: Optional[str]) -> dict:
        payload = {
            "personalizations": [{"to": [{"email": to}]}],
            "from": {"email": from_email or self.config.credentials.get("from_email", "noreply@example.com")},
            "subject": subject,
            "content": [{"type": "text/html", "value": body_html}],
        }

        try:
            resp = await self.http.post("/v3/mail/send", json=payload)
            return {"success": resp.status_code in (200, 202), "status_code": resp.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _send_mailgun(self, to: str, subject: str, body_html: str, from_email: Optional[str]) -> dict:
        domain = self.config.credentials.get("domain", "")
        payload = {
            "from": from_email or self.config.credentials.get("from_email", f"noreply@{domain}"),
            "to": [to],
            "subject": subject,
            "html": body_html,
        }

        try:
            resp = await self.http.post(f"/v3/{domain}/messages", data=payload)
            return {"success": resp.status_code == 200, "status_code": resp.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}


class PaymentIntegration(BaseIntegration):
    """Payment gateway integration (Stripe-compatible)."""

    async def create_payment_intent(self, amount: int, currency: str = "usd", metadata: Optional[dict] = None) -> dict:
        payload = {
            "amount": amount,
            "currency": currency,
            "metadata": metadata or {},
        }

        try:
            resp = await self.http.post("/v1/payment_intents", json=payload)
            resp.raise_for_status()
            return {"success": True, "data": resp.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def refund(self, payment_id: str, amount: Optional[int] = None) -> dict:
        payload = {"payment_intent": payment_id}
        if amount:
            payload["amount"] = amount

        try:
            resp = await self.http.post("/v1/refunds", json=payload)
            resp.raise_for_status()
            return {"success": True, "data": resp.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}


class ShippingIntegration(BaseIntegration):
    """Shipping provider integration."""

    async def get_rates(self, origin: dict, destination: dict, parcels: list[dict]) -> dict:
        payload = {
            "origin": origin,
            "destination": destination,
            "parcels": parcels,
        }

        try:
            resp = await self.http.post("/v1/rates", json=payload)
            resp.raise_for_status()
            return {"success": True, "rates": resp.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def create_shipment(self, order: dict) -> dict:
        try:
            resp = await self.http.post("/v1/shipments", json=order)
            resp.raise_for_status()
            return {"success": True, "shipment": resp.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def track(self, tracking_number: str) -> dict:
        try:
            resp = await self.http.get(f"/v1/tracking/{tracking_number}")
            resp.raise_for_status()
            return {"success": True, "tracking": resp.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}


class AccountingIntegration(BaseIntegration):
    """External accounting system integration (QuickBooks, Xero-style)."""

    async def sync_invoice(self, invoice: dict) -> dict:
        try:
            resp = await self.http.post("/v1/invoices", json=invoice)
            resp.raise_for_status()
            return {"success": True, "external_id": resp.json().get("id")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def sync_payment(self, payment: dict) -> dict:
        try:
            resp = await self.http.post("/v1/payments", json=payment)
            resp.raise_for_status()
            return {"success": True, "external_id": resp.json().get("id")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_accounts(self) -> dict:
        try:
            resp = await self.http.get("/v1/accounts")
            resp.raise_for_status()
            return {"success": True, "accounts": resp.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}


INTEGRATION_TYPES = {
    "slack": SlackIntegration,
    "email": EmailIntegration,
    "payment": PaymentIntegration,
    "shipping": ShippingIntegration,
    "accounting": AccountingIntegration,
}


class IntegrationManager:
    """Manages all third-party integrations."""

    def __init__(self):
        self._integrations: dict[str, BaseIntegration] = {}

    def register(
        self,
        name: str,
        provider: str,
        base_url: str,
        auth_type: str,
        credentials: dict,
        headers: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> BaseIntegration:
        config = IntegrationConfig(
            name=name,
            provider=provider,
            base_url=base_url,
            auth_type=auth_type,
            credentials=credentials,
            headers=headers or {},
            metadata=metadata or {},
        )

        integration_class = INTEGRATION_TYPES.get(provider, BaseIntegration)
        integration = integration_class(config)
        self._integrations[name] = integration

        logger.info("Integration registered: %s (provider=%s)", name, provider)
        return integration

    def get(self, name: str) -> Optional[BaseIntegration]:
        return self._integrations.get(name)

    def list_integrations(self) -> list[dict]:
        return [
            {
                "name": name,
                "provider": integ.config.provider,
                "base_url": integ.config.base_url,
                "auth_type": integ.config.auth_type,
                "is_active": integ.config.is_active,
            }
            for name, integ in self._integrations.items()
        ]

    def remove(self, name: str) -> bool:
        if name in self._integrations:
            del self._integrations[name]
            return True
        return False

    async def health_check_all(self) -> dict:
        results = {}
        for name, integ in self._integrations.items():
            results[name] = await integ.health_check()
        return results

    async def close_all(self):
        for integ in self._integrations.values():
            await integ.close()


integration_manager = IntegrationManager()
