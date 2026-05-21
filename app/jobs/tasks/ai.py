import os
import logging
import json
from datetime import datetime, timezone

from app.jobs.celery_app import celery_app
from app.jobs.base import BaseTask

logger = logging.getLogger("jobs.ai")

AI_API_URL = os.getenv("AI_API_URL", "http://localhost:8001")
AI_API_KEY = os.getenv("AI_API_KEY", "")


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="app.jobs.tasks.ai.process_natural_language_query",
    soft_time_limit=60,
    time_limit=120,
)
def process_natural_language_query(
    self,
    tenant_id: str,
    user_id: str,
    conversation_id: str | None,
    query: str,
):
    import httpx

    start_time = datetime.now(timezone.utc)

    response = httpx.post(
        f"{AI_API_URL}/v1/query",
        json={
            "tenant_id": tenant_id,
            "query": query,
            "conversation_id": conversation_id,
        },
        headers={"Authorization": f"Bearer {AI_API_KEY}"},
        timeout=90,
    )
    response.raise_for_status()
    result = response.json()

    execution_time = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

    _log_ai_interaction(
        user_id=user_id,
        conversation_id=conversation_id,
        query=query,
        response_data=result,
        execution_time_ms=execution_time,
    )

    logger.info("AI query processed for user %s in %dms", user_id, execution_time)
    return {
        "response": result.get("answer"),
        "sql": result.get("generated_sql"),
        "confidence": result.get("confidence"),
        "execution_time_ms": execution_time,
    }


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="app.jobs.tasks.ai.generate_embeddings",
    soft_time_limit=120,
    time_limit=300,
)
def generate_embeddings(
    self,
    texts: list[str],
    model: str = "text-embedding-3-small",
):
    import httpx

    response = httpx.post(
        f"{AI_API_URL}/v1/embeddings",
        json={"texts": texts, "model": model},
        headers={"Authorization": f"Bearer {AI_API_KEY}"},
        timeout=120,
    )
    response.raise_for_status()
    result = response.json()

    logger.info("Generated %d embeddings", len(texts))
    return {"count": len(texts), "dimensions": len(result["embeddings"][0]) if result.get("embeddings") else 0}


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="app.jobs.tasks.ai.train_on_feedback",
    soft_time_limit=300,
    time_limit=600,
)
def train_on_feedback(self, feedback_batch: list[dict]):
    import httpx

    response = httpx.post(
        f"{AI_API_URL}/v1/train",
        json={"feedback": feedback_batch},
        headers={"Authorization": f"Bearer {AI_API_KEY}"},
        timeout=300,
    )
    response.raise_for_status()

    logger.info("Training completed on %d feedback items", len(feedback_batch))
    return {"trained_items": len(feedback_batch), "status": "completed"}


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="app.jobs.tasks.ai.analyze_sales_trends",
    soft_time_limit=120,
    time_limit=240,
)
def analyze_sales_trends(self, tenant_id: str, period_months: int = 6):
    import httpx

    response = httpx.post(
        f"{AI_API_URL}/v1/analyze/sales",
        json={"tenant_id": tenant_id, "period_months": period_months},
        headers={"Authorization": f"Bearer {AI_API_KEY}"},
        timeout=120,
    )
    response.raise_for_status()

    logger.info("Sales trend analysis completed for tenant %s", tenant_id)
    return response.json()


def _log_ai_interaction(
    user_id: str,
    conversation_id: str | None,
    query: str,
    response_data: dict,
    execution_time_ms: int,
):
    try:
        from app.core.database import get_sync_engine
        from sqlalchemy import text

        engine = get_sync_engine()
        with engine.connect() as conn:
            conn.execute(
                text(
                    "INSERT INTO ai_logs (user_id, conversation_id, user_query, "
                    "generated_sql, ai_response, detected_intent, confidence_score, "
                    "execution_time_ms, created_at) "
                    "VALUES (:user_id, :conv_id, :query, :sql, :response, "
                    ":intent, :confidence, :exec_time, NOW())"
                ),
                {
                    "user_id": user_id,
                    "conv_id": conversation_id,
                    "query": query,
                    "sql": response_data.get("generated_sql"),
                    "response": response_data.get("answer"),
                    "intent": response_data.get("detected_intent"),
                    "confidence": response_data.get("confidence"),
                    "exec_time": execution_time_ms,
                },
            )
            conn.commit()
    except Exception as e:
        logger.warning("Failed to log AI interaction: %s", e)
