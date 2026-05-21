import logging
from datetime import datetime, timezone
from sqlalchemy import text

logger = logging.getLogger("jobs.tracker")


def create_job_record(
    tenant_id: str | None,
    job_type: str,
    payload: dict | None = None,
    task_id: str | None = None,
) -> str | None:
    try:
        from app.core.database import get_sync_engine
        engine = get_sync_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "INSERT INTO background_jobs (tenant_id, job_type, payload, status) "
                    "VALUES (:tenant_id, :job_type, :payload, 'pending') RETURNING id"
                ),
                {
                    "tenant_id": tenant_id,
                    "job_type": job_type,
                    "payload": str(payload) if payload else None,
                },
            )
            conn.commit()
            row = result.fetchone()
            return str(row[0]) if row else None
    except Exception as e:
        logger.warning(f"Failed to create job record: {e}")
        return None


def update_job_status(task_id: str, status: str, error_message: str | None = None):
    try:
        from app.core.database import get_sync_engine
        engine = get_sync_engine()
        with engine.connect() as conn:
            conn.execute(
                text(
                    "UPDATE background_jobs SET status = :status, "
                    "error_message = :error, processed_at = :now "
                    "WHERE id = :task_id OR payload LIKE :task_pattern"
                ),
                {
                    "status": status,
                    "error": error_message,
                    "now": datetime.now(timezone.utc),
                    "task_id": task_id,
                    "task_pattern": f"%{task_id}%",
                },
            )
            conn.commit()
    except Exception as e:
        logger.warning(f"Failed to update job status: {e}")
