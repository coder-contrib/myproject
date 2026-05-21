import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import ai_client
from app.ai.config import ai_config

logger = logging.getLogger("ai.embeddings")

CREATE_EXTENSION_SQL = "CREATE EXTENSION IF NOT EXISTS vector;"

CREATE_EMBEDDINGS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ai_embeddings (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    content_text TEXT NOT NULL,
    embedding vector({dimensions}),
    metadata JSONB DEFAULT '{{}}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, entity_type, entity_id)
);
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_embeddings_tenant_type
    ON ai_embeddings(tenant_id, entity_type);
CREATE INDEX IF NOT EXISTS idx_embeddings_vector
    ON ai_embeddings USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
"""


class EmbeddingService:
    """Manages vector embeddings with pgvector."""

    async def initialize(self, db: AsyncSession):
        await db.execute(text(CREATE_EXTENSION_SQL))
        await db.execute(text(
            CREATE_EMBEDDINGS_TABLE_SQL.format(dimensions=ai_config.embedding_dimensions)
        ))
        await db.execute(text(CREATE_INDEX_SQL))
        await db.commit()

    async def upsert_embedding(
        self,
        db: AsyncSession,
        tenant_id: str,
        entity_type: str,
        entity_id: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> int:
        import hashlib
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        existing = await db.execute(text(
            "SELECT id, content_hash FROM ai_embeddings "
            "WHERE tenant_id = :tenant_id AND entity_type = :entity_type AND entity_id = :entity_id"
        ), {"tenant_id": tenant_id, "entity_type": entity_type, "entity_id": entity_id})
        row = existing.fetchone()

        if row and row.content_hash == content_hash:
            return row.id

        embedding = await ai_client.create_embedding(content)
        embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"

        if row:
            await db.execute(text(
                "UPDATE ai_embeddings SET content_hash = :hash, content_text = :content, "
                "embedding = :embedding, metadata = :metadata, updated_at = NOW() "
                "WHERE id = :id"
            ), {
                "id": row.id,
                "hash": content_hash,
                "content": content,
                "embedding": embedding_str,
                "metadata": metadata or {},
            })
            await db.commit()
            return row.id
        else:
            result = await db.execute(text(
                "INSERT INTO ai_embeddings (tenant_id, entity_type, entity_id, content_hash, "
                "content_text, embedding, metadata) "
                "VALUES (:tenant_id, :entity_type, :entity_id, :hash, :content, :embedding, :metadata) "
                "RETURNING id"
            ), {
                "tenant_id": tenant_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "hash": content_hash,
                "content": content,
                "embedding": embedding_str,
                "metadata": metadata or {},
            })
            await db.commit()
            return result.scalar()

    async def search_similar(
        self,
        db: AsyncSession,
        tenant_id: str,
        query: str,
        entity_type: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.7,
    ) -> list[dict]:
        query_embedding = await ai_client.create_embedding(query)
        embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

        sql = """
            SELECT id, entity_type, entity_id, content_text, metadata,
                   1 - (embedding <=> :embedding::vector) AS similarity
            FROM ai_embeddings
            WHERE tenant_id = :tenant_id
        """
        params = {"tenant_id": tenant_id, "embedding": embedding_str}

        if entity_type:
            sql += " AND entity_type = :entity_type"
            params["entity_type"] = entity_type

        sql += " AND 1 - (embedding <=> :embedding::vector) >= :threshold"
        params["threshold"] = threshold

        sql += " ORDER BY embedding <=> :embedding::vector LIMIT :limit"
        params["limit"] = limit

        result = await db.execute(text(sql), params)
        rows = result.fetchall()

        return [
            {
                "id": row.id,
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "content": row.content_text,
                "metadata": row.metadata,
                "similarity": float(row.similarity),
            }
            for row in rows
        ]

    async def delete_embedding(
        self,
        db: AsyncSession,
        tenant_id: str,
        entity_type: str,
        entity_id: str,
    ):
        await db.execute(text(
            "DELETE FROM ai_embeddings "
            "WHERE tenant_id = :tenant_id AND entity_type = :entity_type AND entity_id = :entity_id"
        ), {"tenant_id": tenant_id, "entity_type": entity_type, "entity_id": entity_id})
        await db.commit()

    async def bulk_upsert(
        self,
        db: AsyncSession,
        tenant_id: str,
        entity_type: str,
        items: list[dict],
    ) -> int:
        import hashlib
        texts = [item["content"] for item in items]
        embeddings = await ai_client.create_embeddings_batch(texts)
        count = 0

        for item, embedding in zip(items, embeddings):
            content_hash = hashlib.sha256(item["content"].encode()).hexdigest()
            embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"

            await db.execute(text(
                "INSERT INTO ai_embeddings (tenant_id, entity_type, entity_id, content_hash, "
                "content_text, embedding, metadata) "
                "VALUES (:tenant_id, :entity_type, :entity_id, :hash, :content, :embedding, :metadata) "
                "ON CONFLICT (tenant_id, entity_type, entity_id) "
                "DO UPDATE SET content_hash = :hash, content_text = :content, "
                "embedding = :embedding, metadata = :metadata, updated_at = NOW()"
            ), {
                "tenant_id": tenant_id,
                "entity_type": entity_type,
                "entity_id": item["entity_id"],
                "hash": content_hash,
                "content": item["content"],
                "embedding": embedding_str,
                "metadata": item.get("metadata", {}),
            })
            count += 1

        await db.commit()
        return count


embedding_service = EmbeddingService()
