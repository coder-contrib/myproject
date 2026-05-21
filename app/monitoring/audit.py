import uuid
import json
import logging
from typing import Optional
from datetime import datetime, timezone
from collections import deque
from dataclasses import dataclass, field

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.monitoring.config import monitoring_config

logger = logging.getLogger("monitoring.audit")

CREATE_AUDIT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id VARCHAR(100),
    changes JSONB,
    previous_values JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    request_id VARCHAR(36),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_audit_tenant_time ON audit_logs(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(tenant_id, user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_logs(tenant_id, entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action, created_at DESC);
"""


@dataclass
class AuditEntry:
    tenant_id: str
    user_id: str
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    changes: Optional[dict] = None
    previous_values: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class AuditLogger:
    """Records and queries audit trail for compliance and security."""

    def __init__(self, buffer_size: int = 1000):
        self._buffer: deque = deque(maxlen=buffer_size)

    async def initialize(self, db: AsyncSession):
        await db.execute(text(CREATE_AUDIT_TABLE_SQL))
        await db.commit()

    async def log(
        self,
        db: AsyncSession,
        entry: AuditEntry,
    ) -> int:
        if not monitoring_config.audit_log_enabled:
            return 0

        result = await db.execute(text(
            "INSERT INTO audit_logs "
            "(tenant_id, user_id, action, entity_type, entity_id, changes, "
            "previous_values, ip_address, user_agent, request_id, metadata) "
            "VALUES (:tenant_id, :user_id, :action, :entity_type, :entity_id, "
            ":changes, :previous_values, :ip_address, :user_agent, :request_id, :metadata) "
            "RETURNING id"
        ), {
            "tenant_id": entry.tenant_id,
            "user_id": entry.user_id,
            "action": entry.action,
            "entity_type": entry.entity_type,
            "entity_id": entry.entity_id,
            "changes": entry.changes,
            "previous_values": entry.previous_values,
            "ip_address": entry.ip_address,
            "user_agent": entry.user_agent,
            "request_id": entry.request_id,
            "metadata": entry.metadata,
        })
        await db.commit()

        audit_id = result.scalar()
        self._buffer.append({
            "id": audit_id,
            "action": entry.action,
            "entity_type": entry.entity_type,
            "user_id": entry.user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return audit_id

    async def query(
        self,
        db: AsyncSession,
        tenant_id: str,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        sql = "SELECT * FROM audit_logs WHERE tenant_id = :tenant_id"
        params = {"tenant_id": tenant_id, "limit": limit, "offset": offset}

        if user_id:
            sql += " AND user_id = :user_id"
            params["user_id"] = user_id
        if action:
            sql += " AND action = :action"
            params["action"] = action
        if entity_type:
            sql += " AND entity_type = :entity_type"
            params["entity_type"] = entity_type
        if entity_id:
            sql += " AND entity_id = :entity_id"
            params["entity_id"] = entity_id
        if start_date:
            sql += " AND created_at >= :start_date"
            params["start_date"] = start_date
        if end_date:
            sql += " AND created_at <= :end_date"
            params["end_date"] = end_date

        sql += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"

        result = await db.execute(text(sql), params)
        rows = result.fetchall()
        columns = list(result.keys())
        return [dict(zip(columns, row)) for row in rows]

    async def get_user_activity(
        self,
        db: AsyncSession,
        tenant_id: str,
        user_id: str,
        days: int = 30,
    ) -> dict:
        sql = """
            SELECT action, COUNT(*) as count, MAX(created_at) as last_at
            FROM audit_logs
            WHERE tenant_id = :tenant_id AND user_id = :user_id
              AND created_at >= NOW() - make_interval(days => :days)
            GROUP BY action
            ORDER BY count DESC
        """

        result = await db.execute(text(sql), {
            "tenant_id": tenant_id, "user_id": user_id, "days": days,
        })
        rows = result.fetchall()
        columns = list(result.keys())
        return {
            "user_id": user_id,
            "period_days": days,
            "actions": [dict(zip(columns, row)) for row in rows],
        }

    async def get_entity_history(
        self,
        db: AsyncSession,
        tenant_id: str,
        entity_type: str,
        entity_id: str,
        limit: int = 50,
    ) -> list[dict]:
        return await self.query(
            db=db,
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
        )

    async def cleanup_old_entries(
        self,
        db: AsyncSession,
        tenant_id: str,
        retention_days: Optional[int] = None,
    ) -> int:
        days = retention_days or monitoring_config.audit_retention_days
        result = await db.execute(text(
            "DELETE FROM audit_logs WHERE tenant_id = :tenant_id "
            "AND created_at < NOW() - make_interval(days => :days)"
        ), {"tenant_id": tenant_id, "days": days})
        await db.commit()
        return result.rowcount


audit_logger = AuditLogger()
