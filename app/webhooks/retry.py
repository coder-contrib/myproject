import logging
import math
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.webhooks.config import webhook_config

logger = logging.getLogger("webhooks.retry")


@dataclass
class RetryPolicy:
    """Configurable retry policy with exponential backoff and jitter."""
    max_retries: int = webhook_config.max_retries
    base_delay: int = webhook_config.retry_base_delay
    max_delay: int = webhook_config.retry_max_delay
    backoff_factor: float = 2.0
    jitter: bool = True

    def get_delay(self, attempt: int) -> int:
        """Calculate delay for a given retry attempt using exponential backoff."""
        delay = self.base_delay * (self.backoff_factor ** attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            import random
            delay = delay * (0.5 + random.random() * 0.5)

        return int(delay)

    def should_retry(self, attempt: int, status_code: Optional[int] = None) -> bool:
        """Determine if a delivery should be retried."""
        if attempt >= self.max_retries:
            return False

        # Don't retry client errors (4xx) except specific ones
        if status_code and 400 <= status_code < 500:
            # Retry 429 (rate limited) and 408 (timeout)
            return status_code in (408, 429)

        return True

    def get_next_attempt_time(self, attempt: int) -> datetime:
        """Get the datetime for the next retry attempt."""
        delay = self.get_delay(attempt)
        return datetime.utcnow() + timedelta(seconds=delay)


CREATE_DELIVERY_LOG_SQL = """
CREATE TABLE IF NOT EXISTS webhook_deliveries (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    webhook_id VARCHAR(36) NOT NULL,
    delivery_id VARCHAR(36) NOT NULL UNIQUE,
    event_type VARCHAR(100) NOT NULL,
    endpoint_url TEXT NOT NULL,
    payload JSONB NOT NULL,
    attempt INTEGER DEFAULT 1,
    max_attempts INTEGER DEFAULT 5,
    status VARCHAR(20) DEFAULT 'pending',
    response_status INTEGER,
    response_body TEXT,
    response_time_ms INTEGER,
    error_message TEXT,
    next_retry_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_deliveries_status ON webhook_deliveries(status, next_retry_at);
CREATE INDEX IF NOT EXISTS idx_deliveries_webhook ON webhook_deliveries(webhook_id, created_at);
CREATE INDEX IF NOT EXISTS idx_deliveries_tenant ON webhook_deliveries(tenant_id, event_type);
"""


class WebhookRetryManager:
    """Manages webhook delivery retries with persistence."""

    def __init__(self, policy: Optional[RetryPolicy] = None):
        self.policy = policy or RetryPolicy()

    async def initialize(self, db: AsyncSession):
        await db.execute(text(CREATE_DELIVERY_LOG_SQL))
        await db.commit()

    async def record_delivery(
        self,
        db: AsyncSession,
        tenant_id: str,
        webhook_id: str,
        delivery_id: str,
        event_type: str,
        endpoint_url: str,
        payload: dict,
    ):
        await db.execute(text(
            "INSERT INTO webhook_deliveries "
            "(tenant_id, webhook_id, delivery_id, event_type, endpoint_url, payload, max_attempts) "
            "VALUES (:tenant_id, :webhook_id, :delivery_id, :event_type, :url, :payload, :max_attempts)"
        ), {
            "tenant_id": tenant_id,
            "webhook_id": webhook_id,
            "delivery_id": delivery_id,
            "event_type": event_type,
            "url": endpoint_url,
            "payload": payload,
            "max_attempts": self.policy.max_retries,
        })
        await db.commit()

    async def record_success(
        self,
        db: AsyncSession,
        delivery_id: str,
        status_code: int,
        response_body: str,
        response_time_ms: int,
    ):
        await db.execute(text(
            "UPDATE webhook_deliveries SET "
            "status = 'delivered', response_status = :status, "
            "response_body = :body, response_time_ms = :time_ms, "
            "completed_at = NOW() "
            "WHERE delivery_id = :delivery_id"
        ), {
            "delivery_id": delivery_id,
            "status": status_code,
            "body": response_body[:5000],
            "time_ms": response_time_ms,
        })
        await db.commit()

    async def record_failure(
        self,
        db: AsyncSession,
        delivery_id: str,
        attempt: int,
        status_code: Optional[int],
        error_message: str,
        response_time_ms: int,
    ):
        should_retry = self.policy.should_retry(attempt, status_code)

        if should_retry:
            next_retry = self.policy.get_next_attempt_time(attempt)
            await db.execute(text(
                "UPDATE webhook_deliveries SET "
                "status = 'retrying', attempt = :attempt, "
                "response_status = :status, error_message = :error, "
                "response_time_ms = :time_ms, next_retry_at = :next_retry "
                "WHERE delivery_id = :delivery_id"
            ), {
                "delivery_id": delivery_id,
                "attempt": attempt,
                "status": status_code,
                "error": error_message[:2000],
                "time_ms": response_time_ms,
                "next_retry": next_retry,
            })
        else:
            await db.execute(text(
                "UPDATE webhook_deliveries SET "
                "status = 'failed', attempt = :attempt, "
                "response_status = :status, error_message = :error, "
                "response_time_ms = :time_ms, completed_at = NOW() "
                "WHERE delivery_id = :delivery_id"
            ), {
                "delivery_id": delivery_id,
                "attempt": attempt,
                "status": status_code,
                "error": error_message[:2000],
                "time_ms": response_time_ms,
            })

        await db.commit()
        return should_retry

    async def get_pending_retries(self, db: AsyncSession, limit: int = 50) -> list[dict]:
        result = await db.execute(text(
            "SELECT id, tenant_id, webhook_id, delivery_id, event_type, "
            "endpoint_url, payload, attempt "
            "FROM webhook_deliveries "
            "WHERE status = 'retrying' AND next_retry_at <= NOW() "
            "ORDER BY next_retry_at "
            "LIMIT :limit"
        ), {"limit": limit})

        rows = result.fetchall()
        columns = list(result.keys())
        return [dict(zip(columns, row)) for row in rows]

    async def get_delivery_log(
        self,
        db: AsyncSession,
        tenant_id: str,
        webhook_id: Optional[str] = None,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        sql = "SELECT * FROM webhook_deliveries WHERE tenant_id = :tenant_id"
        params = {"tenant_id": tenant_id, "limit": limit}

        if webhook_id:
            sql += " AND webhook_id = :webhook_id"
            params["webhook_id"] = webhook_id
        if event_type:
            sql += " AND event_type = :event_type"
            params["event_type"] = event_type
        if status:
            sql += " AND status = :status"
            params["status"] = status

        sql += " ORDER BY created_at DESC LIMIT :limit"

        result = await db.execute(text(sql), params)
        rows = result.fetchall()
        columns = list(result.keys())
        return [dict(zip(columns, row)) for row in rows]

    async def get_stats(
        self,
        db: AsyncSession,
        tenant_id: str,
        days: int = 7,
    ) -> dict:
        sql = """
            SELECT
                status,
                COUNT(*) as count,
                AVG(response_time_ms) as avg_response_time,
                AVG(attempt) as avg_attempts
            FROM webhook_deliveries
            WHERE tenant_id = :tenant_id
              AND created_at >= NOW() - make_interval(days => :days)
            GROUP BY status
        """

        result = await db.execute(text(sql), {"tenant_id": tenant_id, "days": days})
        rows = result.fetchall()

        stats = {}
        for row in rows:
            stats[row.status] = {
                "count": row.count,
                "avg_response_time_ms": round(float(row.avg_response_time or 0), 1),
                "avg_attempts": round(float(row.avg_attempts or 0), 1),
            }

        return {"period_days": days, "stats": stats}


retry_manager = WebhookRetryManager()
