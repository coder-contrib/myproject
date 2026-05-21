import logging
from datetime import datetime, timezone, timedelta

from app.jobs.celery_app import celery_app
from app.jobs.base import BaseTask

logger = logging.getLogger("jobs.maintenance")


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="app.jobs.tasks.maintenance.cleanup_expired_jobs",
)
def cleanup_expired_jobs(self, retention_days: int = 30):
    from app.core.database import get_sync_engine
    from sqlalchemy import text

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    engine = get_sync_engine()

    with engine.connect() as conn:
        result = conn.execute(
            text(
                "DELETE FROM background_jobs "
                "WHERE status IN ('completed', 'failed') AND processed_at < :cutoff"
            ),
            {"cutoff": cutoff},
        )
        deleted = result.rowcount
        conn.commit()

    logger.info("Cleaned up %d expired job records", deleted)
    return {"deleted": deleted, "cutoff": cutoff.isoformat()}


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="app.jobs.tasks.maintenance.cleanup_expired_sessions",
)
def cleanup_expired_sessions(self):
    from app.core.database import get_sync_engine
    from sqlalchemy import text

    engine = get_sync_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text("DELETE FROM user_sessions WHERE expires_at < NOW()")
        )
        deleted = result.rowcount
        conn.commit()

    logger.info("Cleaned up %d expired sessions", deleted)
    return {"deleted_sessions": deleted}


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="app.jobs.tasks.maintenance.refresh_materialized_views",
)
def refresh_materialized_views(self):
    from app.core.database import get_sync_engine
    from sqlalchemy import text

    views = [
        "monthly_sales_summary",
        "monthly_purchase_summary",
        "product_profit_summary",
        "treasury_balances",
        "account_balances",
    ]

    engine = get_sync_engine()
    refreshed = []

    with engine.connect() as conn:
        for view in views:
            try:
                conn.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}"))
                refreshed.append(view)
            except Exception as e:
                try:
                    conn.execute(text(f"REFRESH MATERIALIZED VIEW {view}"))
                    refreshed.append(view)
                except Exception as e2:
                    logger.warning("Failed to refresh %s: %s", view, e2)
        conn.commit()

    logger.info("Refreshed %d materialized views", len(refreshed))
    return {"refreshed": refreshed}
