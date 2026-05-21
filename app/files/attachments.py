import uuid
import logging
from typing import Optional
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.files.storage import get_storage

logger = logging.getLogger("files.attachments")

CREATE_FILES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS files (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    uploaded_by VARCHAR(100) NOT NULL,
    filename VARCHAR(500) NOT NULL,
    storage_key VARCHAR(1000) NOT NULL UNIQUE,
    content_type VARCHAR(200) NOT NULL,
    size BIGINT NOT NULL,
    etag VARCHAR(64),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_files_tenant ON files(tenant_id);
CREATE INDEX IF NOT EXISTS idx_files_uploaded_by ON files(tenant_id, uploaded_by);
"""

CREATE_ATTACHMENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS attachments (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    file_id VARCHAR(36) NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    label VARCHAR(200),
    sort_order INTEGER DEFAULT 0,
    attached_by VARCHAR(100) NOT NULL,
    attached_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_attachments_entity
    ON attachments(tenant_id, entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_attachments_file
    ON attachments(file_id);
"""


class AttachmentService:
    """Links files to business entities (invoices, products, orders, etc.)."""

    async def initialize(self, db: AsyncSession):
        await db.execute(text(CREATE_FILES_TABLE_SQL))
        await db.execute(text(CREATE_ATTACHMENTS_TABLE_SQL))
        await db.commit()

    async def attach(
        self,
        db: AsyncSession,
        tenant_id: str,
        file_id: str,
        entity_type: str,
        entity_id: str,
        user_id: str,
        label: Optional[str] = None,
        sort_order: int = 0,
    ) -> dict:
        # Verify file exists and belongs to tenant
        file_check = await db.execute(text(
            "SELECT id, filename, content_type, size FROM files "
            "WHERE id = :file_id AND tenant_id = :tenant_id"
        ), {"file_id": file_id, "tenant_id": tenant_id})
        file_row = file_check.fetchone()

        if not file_row:
            return {"success": False, "error": "File not found"}

        attachment_id = str(uuid.uuid4())
        await db.execute(text(
            "INSERT INTO attachments (id, tenant_id, file_id, entity_type, entity_id, "
            "label, sort_order, attached_by) "
            "VALUES (:id, :tenant_id, :file_id, :entity_type, :entity_id, "
            ":label, :sort_order, :user_id)"
        ), {
            "id": attachment_id,
            "tenant_id": tenant_id,
            "file_id": file_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "label": label,
            "sort_order": sort_order,
            "user_id": user_id,
        })
        await db.commit()

        logger.info(
            "File attached: attachment=%s file=%s entity=%s:%s",
            attachment_id, file_id, entity_type, entity_id,
        )

        return {
            "success": True,
            "attachment": {
                "id": attachment_id,
                "file_id": file_id,
                "filename": file_row.filename,
                "content_type": file_row.content_type,
                "size": file_row.size,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "label": label,
            },
        }

    async def detach(
        self,
        db: AsyncSession,
        tenant_id: str,
        attachment_id: str,
    ) -> bool:
        result = await db.execute(text(
            "DELETE FROM attachments WHERE id = :id AND tenant_id = :tenant_id"
        ), {"id": attachment_id, "tenant_id": tenant_id})
        await db.commit()
        return result.rowcount > 0

    async def get_entity_attachments(
        self,
        db: AsyncSession,
        tenant_id: str,
        entity_type: str,
        entity_id: str,
    ) -> list[dict]:
        result = await db.execute(text(
            "SELECT a.id, a.file_id, a.label, a.sort_order, a.attached_by, a.attached_at, "
            "f.filename, f.content_type, f.size, f.storage_key "
            "FROM attachments a "
            "JOIN files f ON a.file_id = f.id "
            "WHERE a.tenant_id = :tenant_id AND a.entity_type = :entity_type "
            "AND a.entity_id = :entity_id "
            "ORDER BY a.sort_order, a.attached_at"
        ), {"tenant_id": tenant_id, "entity_type": entity_type, "entity_id": entity_id})

        rows = result.fetchall()
        columns = list(result.keys())
        return [dict(zip(columns, row)) for row in rows]

    async def get_file_attachments(
        self,
        db: AsyncSession,
        tenant_id: str,
        file_id: str,
    ) -> list[dict]:
        result = await db.execute(text(
            "SELECT id, entity_type, entity_id, label, attached_by, attached_at "
            "FROM attachments "
            "WHERE tenant_id = :tenant_id AND file_id = :file_id "
            "ORDER BY attached_at"
        ), {"tenant_id": tenant_id, "file_id": file_id})

        rows = result.fetchall()
        columns = list(result.keys())
        return [dict(zip(columns, row)) for row in rows]

    async def reorder(
        self,
        db: AsyncSession,
        tenant_id: str,
        entity_type: str,
        entity_id: str,
        attachment_ids: list[str],
    ) -> bool:
        for order, attachment_id in enumerate(attachment_ids):
            await db.execute(text(
                "UPDATE attachments SET sort_order = :order "
                "WHERE id = :id AND tenant_id = :tenant_id "
                "AND entity_type = :entity_type AND entity_id = :entity_id"
            ), {
                "order": order,
                "id": attachment_id,
                "tenant_id": tenant_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
            })
        await db.commit()
        return True

    async def copy_attachments(
        self,
        db: AsyncSession,
        tenant_id: str,
        source_type: str,
        source_id: str,
        target_type: str,
        target_id: str,
        user_id: str,
    ) -> int:
        """Copy all attachments from one entity to another."""
        attachments = await self.get_entity_attachments(
            db, tenant_id, source_type, source_id
        )

        count = 0
        for att in attachments:
            await self.attach(
                db=db,
                tenant_id=tenant_id,
                file_id=att["file_id"],
                entity_type=target_type,
                entity_id=target_id,
                user_id=user_id,
                label=att["label"],
                sort_order=att["sort_order"],
            )
            count += 1

        return count


attachment_service = AttachmentService()
