import logging
import json
from datetime import datetime, timezone

from app.jobs.celery_app import celery_app
from app.jobs.base import BaseTask

logger = logging.getLogger("jobs.notifications")


@celery_app.task(base=BaseTask, bind=True, name="app.jobs.tasks.notifications.send_notification")
def send_notification(
    self,
    tenant_id: str,
    user_id: str,
    title: str,
    message: str,
    notification_type: str = "info",
    entity_type: str | None = None,
    entity_id: str | None = None,
):
    from app.core.database import get_sync_engine
    from sqlalchemy import text

    engine = get_sync_engine()
    with engine.connect() as conn:
        conn.execute(
            text(
                "INSERT INTO notifications (tenant_id, user_id, title, message, type, is_read) "
                "VALUES (:tenant_id, :user_id, :title, :message, :type, FALSE)"
            ),
            {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "title": title,
                "message": message,
                "type": notification_type,
            },
        )
        conn.commit()

    _push_realtime(tenant_id, user_id, {
        "type": notification_type,
        "title": title,
        "message": message,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    logger.info("Notification sent to user %s: %s", user_id, title)
    return {"user_id": user_id, "title": title, "status": "delivered"}


@celery_app.task(base=BaseTask, bind=True, name="app.jobs.tasks.notifications.send_bulk_notification")
def send_bulk_notification(
    self,
    tenant_id: str,
    user_ids: list[str],
    title: str,
    message: str,
    notification_type: str = "info",
):
    for user_id in user_ids:
        send_notification.delay(
            tenant_id=tenant_id,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
        )

    logger.info("Bulk notification queued for %d users", len(user_ids))
    return {"total_users": len(user_ids), "status": "queued"}


@celery_app.task(base=BaseTask, bind=True, name="app.jobs.tasks.notifications.send_low_stock_alert")
def send_low_stock_alert(
    self,
    tenant_id: str,
    product_id: str,
    product_name: str,
    current_qty: int,
    threshold: int,
    warehouse_name: str,
):
    from app.core.database import get_sync_engine
    from sqlalchemy import text

    engine = get_sync_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT u.id FROM users u "
                "JOIN role_permissions rp ON rp.role_id = u.role_id "
                "JOIN permissions p ON p.id = rp.permission_id "
                "WHERE u.tenant_id = :tenant_id AND p.name = 'inventory.stock.manage' AND u.is_active = TRUE"
            ),
            {"tenant_id": tenant_id},
        )
        managers = [str(row[0]) for row in result.fetchall()]

    title = f"Low Stock: {product_name}"
    message = f"{product_name} at {warehouse_name} has {current_qty} units (threshold: {threshold})"

    for user_id in managers:
        send_notification.delay(
            tenant_id=tenant_id,
            user_id=user_id,
            title=title,
            message=message,
            notification_type="warning",
            entity_type="product",
            entity_id=product_id,
        )

    return {"product": product_name, "notified_users": len(managers)}


def _push_realtime(tenant_id: str, user_id: str, payload: dict):
    try:
        import redis
        import os
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        channel = f"notifications:{tenant_id}:{user_id}"
        r.publish(channel, json.dumps(payload))
    except Exception as e:
        logger.debug("Realtime push failed (non-critical): %s", e)
