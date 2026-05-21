import uuid
import logging
from typing import Optional
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.webhooks.events import WEBHOOK_EVENTS, WebhookEvent
from app.webhooks.signature import WebhookSignature
from app.webhooks.dispatcher import webhook_dispatcher

logger = logging.getLogger("webhooks.registry")

CREATE_WEBHOOKS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS webhooks (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    url TEXT NOT NULL,
    secret VARCHAR(128) NOT NULL,
    events JSONB NOT NULL DEFAULT '[]',
    headers JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_triggered_at TIMESTAMPTZ,
    failure_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_webhooks_tenant ON webhooks(tenant_id, is_active);
CREATE INDEX IF NOT EXISTS idx_webhooks_events ON webhooks USING GIN(events);
"""


class WebhookRegistry:
    """Manages webhook endpoint registrations."""

    async def initialize(self, db: AsyncSession):
        await db.execute(text(CREATE_WEBHOOKS_TABLE_SQL))
        await db.commit()

    async def register(
        self,
        db: AsyncSession,
        tenant_id: str,
        name: str,
        url: str,
        events: list[str],
        created_by: str,
        headers: Optional[dict] = None,
    ) -> dict:
        # Validate event types
        invalid_events = [e for e in events if e not in WEBHOOK_EVENTS and e != "*"]
        if invalid_events:
            return {"success": False, "error": f"Invalid event types: {invalid_events}"}

        webhook_id = str(uuid.uuid4())
        secret = WebhookSignature.generate_secret()

        await db.execute(text(
            "INSERT INTO webhooks (id, tenant_id, name, url, secret, events, headers, created_by) "
            "VALUES (:id, :tenant_id, :name, :url, :secret, :events, :headers, :created_by)"
        ), {
            "id": webhook_id,
            "tenant_id": tenant_id,
            "name": name,
            "url": url,
            "secret": secret,
            "events": events,
            "headers": headers or {},
            "created_by": created_by,
        })
        await db.commit()

        logger.info("Webhook registered: id=%s name=%s url=%s", webhook_id, name, url)

        return {
            "success": True,
            "webhook": {
                "id": webhook_id,
                "name": name,
                "url": url,
                "events": events,
                "secret": secret,
                "is_active": True,
            },
        }

    async def update(
        self,
        db: AsyncSession,
        tenant_id: str,
        webhook_id: str,
        name: Optional[str] = None,
        url: Optional[str] = None,
        events: Optional[list[str]] = None,
        is_active: Optional[bool] = None,
        headers: Optional[dict] = None,
    ) -> bool:
        sets = ["updated_at = NOW()"]
        params = {"id": webhook_id, "tenant_id": tenant_id}

        if name is not None:
            sets.append("name = :name")
            params["name"] = name
        if url is not None:
            sets.append("url = :url")
            params["url"] = url
        if events is not None:
            invalid = [e for e in events if e not in WEBHOOK_EVENTS and e != "*"]
            if invalid:
                return False
            sets.append("events = :events")
            params["events"] = events
        if is_active is not None:
            sets.append("is_active = :is_active")
            params["is_active"] = is_active
        if headers is not None:
            sets.append("headers = :headers")
            params["headers"] = headers

        sql = f"UPDATE webhooks SET {', '.join(sets)} WHERE id = :id AND tenant_id = :tenant_id"
        result = await db.execute(text(sql), params)
        await db.commit()
        return result.rowcount > 0

    async def delete(
        self,
        db: AsyncSession,
        tenant_id: str,
        webhook_id: str,
    ) -> bool:
        result = await db.execute(text(
            "DELETE FROM webhooks WHERE id = :id AND tenant_id = :tenant_id"
        ), {"id": webhook_id, "tenant_id": tenant_id})
        await db.commit()
        return result.rowcount > 0

    async def get(
        self,
        db: AsyncSession,
        tenant_id: str,
        webhook_id: str,
    ) -> Optional[dict]:
        result = await db.execute(text(
            "SELECT * FROM webhooks WHERE id = :id AND tenant_id = :tenant_id"
        ), {"id": webhook_id, "tenant_id": tenant_id})
        row = result.fetchone()
        if not row:
            return None
        columns = list(result.keys())
        return dict(zip(columns, row))

    async def list_webhooks(
        self,
        db: AsyncSession,
        tenant_id: str,
        active_only: bool = False,
    ) -> list[dict]:
        sql = "SELECT id, name, url, events, is_active, created_at, last_triggered_at, failure_count, success_count FROM webhooks WHERE tenant_id = :tenant_id"
        if active_only:
            sql += " AND is_active = TRUE"
        sql += " ORDER BY created_at DESC"

        result = await db.execute(text(sql), {"tenant_id": tenant_id})
        rows = result.fetchall()
        columns = list(result.keys())
        return [dict(zip(columns, row)) for row in rows]

    async def get_subscribers(
        self,
        db: AsyncSession,
        tenant_id: str,
        event_type: str,
    ) -> list[dict]:
        """Get all active webhooks subscribed to a specific event."""
        result = await db.execute(text(
            "SELECT id, url, secret, headers FROM webhooks "
            "WHERE tenant_id = :tenant_id AND is_active = TRUE "
            "AND (events @> :event_json OR events @> '[\"*\"]'::jsonb)"
        ), {
            "tenant_id": tenant_id,
            "event_json": f'["{event_type}"]',
        })
        rows = result.fetchall()
        columns = list(result.keys())
        return [dict(zip(columns, row)) for row in rows]

    async def dispatch_event(
        self,
        db: AsyncSession,
        event: WebhookEvent,
    ) -> int:
        """Dispatch an event to all subscribed webhooks."""
        subscribers = await self.get_subscribers(db, event.tenant_id, event.event_type)

        if not subscribers:
            return 0

        urls_and_secrets = [(sub["url"], sub["secret"]) for sub in subscribers]
        results = await webhook_dispatcher.deliver_to_many(urls_and_secrets, event)

        # Update webhook stats
        for sub, result in zip(subscribers, results):
            if result.success:
                await db.execute(text(
                    "UPDATE webhooks SET success_count = success_count + 1, "
                    "last_triggered_at = NOW() WHERE id = :id"
                ), {"id": sub["id"]})
            else:
                await db.execute(text(
                    "UPDATE webhooks SET failure_count = failure_count + 1, "
                    "last_triggered_at = NOW() WHERE id = :id"
                ), {"id": sub["id"]})

        await db.commit()
        logger.info(
            "Event dispatched: %s -> %d subscribers (%d success)",
            event.event_type, len(subscribers),
            sum(1 for r in results if r.success),
        )

        return len(subscribers)

    async def rotate_secret(
        self,
        db: AsyncSession,
        tenant_id: str,
        webhook_id: str,
    ) -> Optional[str]:
        new_secret = WebhookSignature.generate_secret()
        result = await db.execute(text(
            "UPDATE webhooks SET secret = :secret, updated_at = NOW() "
            "WHERE id = :id AND tenant_id = :tenant_id"
        ), {"id": webhook_id, "tenant_id": tenant_id, "secret": new_secret})
        await db.commit()

        if result.rowcount > 0:
            return new_secret
        return None


webhook_registry = WebhookRegistry()
