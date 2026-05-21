import os
import json
import hmac
import hashlib
import logging
from datetime import datetime, timezone

import httpx

from app.jobs.celery_app import celery_app
from app.jobs.base import BaseTask

logger = logging.getLogger("jobs.webhooks")

WEBHOOK_TIMEOUT = int(os.getenv("WEBHOOK_TIMEOUT", "30"))
WEBHOOK_MAX_RETRIES = int(os.getenv("WEBHOOK_MAX_RETRIES", "5"))


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="app.jobs.tasks.webhooks.deliver_webhook",
    max_retries=5,
    default_retry_delay=60,
)
def deliver_webhook(
    self,
    webhook_id: str,
    event_type: str,
    payload: dict,
    target_url: str,
    secret_key: str | None = None,
):
    body = json.dumps(payload, default=str)
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Event": event_type,
        "X-Webhook-ID": webhook_id,
        "X-Webhook-Timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if secret_key:
        signature = hmac.new(
            secret_key.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()
        headers["X-Webhook-Signature"] = f"sha256={signature}"

    try:
        response = httpx.post(
            target_url,
            content=body,
            headers=headers,
            timeout=WEBHOOK_TIMEOUT,
        )

        _record_delivery(
            webhook_id=webhook_id,
            event_type=event_type,
            payload=payload,
            response_code=response.status_code,
            response_body=response.text[:500],
            attempt=self.request.retries + 1,
            status="delivered" if response.status_code < 400 else "failed",
        )

        if response.status_code >= 400:
            raise Exception(f"Webhook delivery failed: HTTP {response.status_code}")

        logger.info("Webhook delivered: %s -> %s (HTTP %d)", event_type, target_url, response.status_code)
        return {"status": "delivered", "response_code": response.status_code}

    except httpx.TimeoutException:
        _record_delivery(
            webhook_id=webhook_id,
            event_type=event_type,
            payload=payload,
            response_code=0,
            response_body="Timeout",
            attempt=self.request.retries + 1,
            status="retrying",
        )
        raise self.retry(countdown=60 * (2 ** self.request.retries))


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="app.jobs.tasks.webhooks.dispatch_event",
)
def dispatch_event(
    self,
    tenant_id: str,
    event_type: str,
    payload: dict,
):
    from app.core.database import get_sync_engine
    from sqlalchemy import text

    engine = get_sync_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT id, target_url, secret_key_hash FROM webhooks "
                "WHERE tenant_id = :tid AND event_type = :event AND is_active = TRUE"
            ),
            {"tid": tenant_id, "event": event_type},
        )
        webhooks = result.fetchall()

    dispatched = 0
    for wh in webhooks:
        deliver_webhook.delay(
            webhook_id=str(wh[0]),
            event_type=event_type,
            payload=payload,
            target_url=wh[1],
            secret_key=wh[2],
        )
        dispatched += 1

    logger.info("Dispatched event '%s' to %d webhooks for tenant %s", event_type, dispatched, tenant_id)
    return {"event": event_type, "dispatched": dispatched}


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="app.jobs.tasks.webhooks.retry_failed_deliveries",
)
def retry_failed_deliveries(self):
    from app.core.database import get_sync_engine
    from sqlalchemy import text

    engine = get_sync_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT wd.id, wd.webhook_id, wd.event_type, wd.payload, w.target_url, w.secret_key_hash "
                "FROM webhook_deliveries wd "
                "JOIN webhooks w ON w.id = wd.webhook_id "
                "WHERE wd.status = 'failed' AND wd.attempt_count < :max_retries "
                "AND w.is_active = TRUE "
                "ORDER BY wd.created_at LIMIT 50"
            ),
            {"max_retries": WEBHOOK_MAX_RETRIES},
        )
        failed = result.fetchall()

    retried = 0
    for delivery in failed:
        payload = json.loads(delivery[3]) if isinstance(delivery[3], str) else delivery[3]
        deliver_webhook.delay(
            webhook_id=str(delivery[1]),
            event_type=delivery[2],
            payload=payload,
            target_url=delivery[4],
            secret_key=delivery[5],
        )
        retried += 1

    logger.info("Retried %d failed webhook deliveries", retried)
    return {"retried": retried}


def _record_delivery(
    webhook_id: str,
    event_type: str,
    payload: dict,
    response_code: int,
    response_body: str,
    attempt: int,
    status: str,
):
    try:
        from app.core.database import get_sync_engine
        from sqlalchemy import text

        engine = get_sync_engine()
        with engine.connect() as conn:
            conn.execute(
                text(
                    "INSERT INTO webhook_deliveries "
                    "(webhook_id, event_type, payload, response_code, response_body, "
                    "attempt_count, status, delivered_at) "
                    "VALUES (:wid, :event, :payload, :code, :body, :attempt, :status, NOW())"
                ),
                {
                    "wid": webhook_id,
                    "event": event_type,
                    "payload": json.dumps(payload, default=str),
                    "code": response_code,
                    "body": response_body,
                    "attempt": attempt,
                    "status": status,
                },
            )
            conn.commit()
    except Exception as e:
        logger.warning("Failed to record webhook delivery: %s", e)
