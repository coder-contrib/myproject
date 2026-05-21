from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ceramix",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.background_jobs.tasks.send_notification": {"queue": "notifications"},
        "app.background_jobs.tasks.generate_report": {"queue": "reports"},
        "app.background_jobs.tasks.process_webhook": {"queue": "webhooks"},
        "app.background_jobs.tasks.sync_inventory": {"queue": "inventory"},
    },
    beat_schedule={
        "refresh-materialized-views": {
            "task": "app.background_jobs.tasks.refresh_materialized_views",
            "schedule": 300.0,  # every 5 minutes
        },
        "process-outbox-events": {
            "task": "app.background_jobs.tasks.process_outbox_events",
            "schedule": 10.0,
        },
        "check-subscription-expiry": {
            "task": "app.background_jobs.tasks.check_subscription_expiry",
            "schedule": 3600.0,  # hourly
        },
    },
)
