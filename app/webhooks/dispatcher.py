import uuid
import json
import time
import logging
import asyncio
from typing import Optional

import httpx

from app.webhooks.config import webhook_config
from app.webhooks.events import WebhookEvent
from app.webhooks.signature import WebhookSignature

logger = logging.getLogger("webhooks.dispatcher")


@dataclass
class DeliveryResult:
    delivery_id: str
    success: bool
    status_code: Optional[int] = None
    response_body: str = ""
    response_time_ms: int = 0
    error: Optional[str] = None


from dataclasses import dataclass


class WebhookDispatcher:
    """Dispatches webhook events to registered endpoints."""

    def __init__(self):
        self._http: Optional[httpx.AsyncClient] = None
        self._semaphore = asyncio.Semaphore(webhook_config.concurrent_deliveries)

    @property
    def http(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(
                timeout=webhook_config.request_timeout,
                follow_redirects=False,
                headers={"User-Agent": webhook_config.user_agent},
            )
        return self._http

    async def deliver(
        self,
        url: str,
        event: WebhookEvent,
        secret: str,
    ) -> "DeliveryResult":
        """Deliver a single webhook event to an endpoint."""
        delivery_id = str(uuid.uuid4())

        payload = json.dumps({
            "event": event.event_type,
            "timestamp": event.timestamp,
            "tenant_id": event.tenant_id,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "actor_id": event.actor_id,
            "data": event.payload,
            "metadata": event.metadata,
        }, default=str)

        # Enforce payload size limit
        if len(payload.encode()) > webhook_config.max_payload_size:
            return DeliveryResult(
                delivery_id=delivery_id,
                success=False,
                error="Payload exceeds maximum size",
            )

        # Sign the payload
        signature, timestamp = WebhookSignature.sign(payload, secret)

        headers = {
            webhook_config.signature_header: signature,
            webhook_config.timestamp_header: str(timestamp),
            webhook_config.event_header: event.event_type,
            webhook_config.delivery_id_header: delivery_id,
            "Content-Type": "application/json",
        }

        async with self._semaphore:
            start_time = time.time()
            try:
                response = await self.http.post(url, content=payload, headers=headers)
                elapsed_ms = int((time.time() - start_time) * 1000)

                success = 200 <= response.status_code < 300

                if success:
                    logger.info(
                        "Webhook delivered: %s -> %s (status=%d, time=%dms)",
                        event.event_type, url, response.status_code, elapsed_ms,
                    )
                else:
                    logger.warning(
                        "Webhook delivery failed: %s -> %s (status=%d, time=%dms)",
                        event.event_type, url, response.status_code, elapsed_ms,
                    )

                return DeliveryResult(
                    delivery_id=delivery_id,
                    success=success,
                    status_code=response.status_code,
                    response_body=response.text[:5000],
                    response_time_ms=elapsed_ms,
                )

            except httpx.TimeoutException:
                elapsed_ms = int((time.time() - start_time) * 1000)
                logger.warning("Webhook timeout: %s -> %s", event.event_type, url)
                return DeliveryResult(
                    delivery_id=delivery_id,
                    success=False,
                    response_time_ms=elapsed_ms,
                    error="Request timed out",
                )
            except httpx.RequestError as e:
                elapsed_ms = int((time.time() - start_time) * 1000)
                logger.error("Webhook request error: %s -> %s: %s", event.event_type, url, str(e))
                return DeliveryResult(
                    delivery_id=delivery_id,
                    success=False,
                    response_time_ms=elapsed_ms,
                    error=str(e),
                )

    async def deliver_to_many(
        self,
        urls_and_secrets: list[tuple[str, str]],
        event: WebhookEvent,
    ) -> list["DeliveryResult"]:
        """Deliver a webhook event to multiple endpoints concurrently."""
        tasks = [
            self.deliver(url, event, secret)
            for url, secret in urls_and_secrets
        ]
        return await asyncio.gather(*tasks)

    async def close(self):
        if self._http and not self._http.is_closed:
            await self._http.aclose()


webhook_dispatcher = WebhookDispatcher()
