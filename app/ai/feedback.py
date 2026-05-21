import logging
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("ai.feedback")

CREATE_FEEDBACK_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ai_feedback (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    interaction_id VARCHAR(100) NOT NULL,
    feature VARCHAR(50) NOT NULL,
    query TEXT,
    response_summary TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback_type VARCHAR(20) DEFAULT 'rating',
    comment TEXT,
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_feedback_tenant_feature
    ON ai_feedback(tenant_id, feature);
CREATE INDEX IF NOT EXISTS idx_feedback_rating
    ON ai_feedback(rating);
"""


@dataclass
class FeedbackEntry:
    tenant_id: str
    user_id: str
    interaction_id: str
    feature: str
    query: str = ""
    response_summary: str = ""
    rating: Optional[int] = None
    feedback_type: str = "rating"
    comment: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class AIFeedbackCollector:
    """Collects and manages user feedback on AI interactions."""

    async def initialize(self, db: AsyncSession):
        await db.execute(text(CREATE_FEEDBACK_TABLE_SQL))
        await db.commit()

    async def submit_feedback(
        self,
        db: AsyncSession,
        entry: FeedbackEntry,
    ) -> int:
        result = await db.execute(text(
            "INSERT INTO ai_feedback (tenant_id, user_id, interaction_id, feature, "
            "query, response_summary, rating, feedback_type, comment, tags, metadata) "
            "VALUES (:tenant_id, :user_id, :interaction_id, :feature, "
            ":query, :response_summary, :rating, :feedback_type, :comment, :tags, :metadata) "
            "RETURNING id"
        ), {
            "tenant_id": entry.tenant_id,
            "user_id": entry.user_id,
            "interaction_id": entry.interaction_id,
            "feature": entry.feature,
            "query": entry.query,
            "response_summary": entry.response_summary,
            "rating": entry.rating,
            "feedback_type": entry.feedback_type,
            "comment": entry.comment,
            "tags": entry.tags,
            "metadata": entry.metadata,
        })
        await db.commit()
        feedback_id = result.scalar()
        logger.info(
            "Feedback submitted: id=%d feature=%s rating=%s user=%s",
            feedback_id, entry.feature, entry.rating, entry.user_id,
        )
        return feedback_id

    async def get_feedback_stats(
        self,
        db: AsyncSession,
        tenant_id: str,
        feature: Optional[str] = None,
        days: int = 30,
    ) -> dict:
        sql = """
            SELECT feature,
                   COUNT(*) as total,
                   AVG(rating) as avg_rating,
                   COUNT(CASE WHEN rating >= 4 THEN 1 END) as positive,
                   COUNT(CASE WHEN rating <= 2 THEN 1 END) as negative
            FROM ai_feedback
            WHERE tenant_id = :tenant_id
              AND created_at >= NOW() - make_interval(days => :days)
        """
        params = {"tenant_id": tenant_id, "days": days}

        if feature:
            sql += " AND feature = :feature"
            params["feature"] = feature

        sql += " GROUP BY feature ORDER BY total DESC"

        result = await db.execute(text(sql), params)
        rows = result.fetchall()

        stats = []
        for row in rows:
            stats.append({
                "feature": row.feature,
                "total_interactions": row.total,
                "avg_rating": round(float(row.avg_rating), 2) if row.avg_rating else None,
                "positive_count": row.positive,
                "negative_count": row.negative,
                "satisfaction_rate": round(row.positive / row.total * 100, 1) if row.total > 0 else 0,
            })

        return {"stats": stats, "period_days": days}

    async def get_recent_feedback(
        self,
        db: AsyncSession,
        tenant_id: str,
        feature: Optional[str] = None,
        limit: int = 50,
        rating_filter: Optional[int] = None,
    ) -> list[dict]:
        sql = """
            SELECT id, user_id, interaction_id, feature, query, response_summary,
                   rating, feedback_type, comment, tags, created_at
            FROM ai_feedback
            WHERE tenant_id = :tenant_id
        """
        params = {"tenant_id": tenant_id, "limit": limit}

        if feature:
            sql += " AND feature = :feature"
            params["feature"] = feature
        if rating_filter:
            sql += " AND rating = :rating"
            params["rating"] = rating_filter

        sql += " ORDER BY created_at DESC LIMIT :limit"

        result = await db.execute(text(sql), params)
        rows = result.fetchall()
        columns = list(result.keys())

        return [dict(zip(columns, row)) for row in rows]

    async def get_improvement_suggestions(
        self,
        db: AsyncSession,
        tenant_id: str,
        feature: str,
    ) -> dict:
        negative_feedback = await self.get_recent_feedback(
            db=db,
            tenant_id=tenant_id,
            feature=feature,
            rating_filter=1,
            limit=20,
        )
        negative_feedback.extend(await self.get_recent_feedback(
            db=db,
            tenant_id=tenant_id,
            feature=feature,
            rating_filter=2,
            limit=20,
        ))

        if not negative_feedback:
            return {
                "feature": feature,
                "suggestions": [],
                "summary": "No negative feedback found. The feature appears to be performing well.",
            }

        from app.ai.client import ai_client
        import json

        feedback_text = json.dumps(
            [{"query": f.get("query"), "comment": f.get("comment"), "rating": f.get("rating")} for f in negative_feedback],
            default=str,
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI product improvement analyst. Analyze negative user feedback "
                    "and suggest specific improvements. Return JSON with: "
                    "suggestions (array of {issue, fix, priority: high|medium|low}), "
                    "patterns (array of recurring complaint themes), summary (string)."
                ),
            },
            {
                "role": "user",
                "content": f"Feature: {feature}\nNegative feedback entries: {feedback_text}",
            },
        ]

        response = await ai_client.chat_completion(
            messages=messages,
            response_format={"type": "json_object"},
        )
        result = ai_client.extract_json(response)
        result["feature"] = feature
        result["feedback_count"] = len(negative_feedback)
        return result


feedback_collector = AIFeedbackCollector()
