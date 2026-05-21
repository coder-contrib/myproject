import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_RESULT_BACKEND = os.getenv("REDIS_RESULT_BACKEND", "redis://localhost:6379/1")

celery_app = Celery(
    "ceramix_erp",
    broker=REDIS_URL,
    backend=REDIS_RESULT_BACKEND,
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
    task_reject_on_worker_lost=True,
    result_expires=86400,
    task_soft_time_limit=300,
    task_time_limit=600,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
    task_routes={
        "app.jobs.tasks.email.*": {"queue": "email"},
        "app.jobs.tasks.notifications.*": {"queue": "notifications"},
        "app.jobs.tasks.ai.*": {"queue": "ai"},
        "app.jobs.tasks.reports.*": {"queue": "reports"},
        "app.jobs.tasks.webhooks.*": {"queue": "webhooks"},
        "app.jobs.tasks.backup.*": {"queue": "backup"},
    },
    task_default_queue="default",
)

celery_app.conf.beat_schedule = {
    "process-scheduled-reports": {
        "task": "app.jobs.tasks.reports.process_scheduled_reports",
        "schedule": 3600.0,
    },
    "daily-backup": {
        "task": "app.jobs.tasks.backup.run_daily_backup",
        "schedule": 86400.0,
    },
    "retry-failed-webhooks": {
        "task": "app.jobs.tasks.webhooks.retry_failed_deliveries",
        "schedule": 300.0,
    },
    "cleanup-expired-jobs": {
        "task": "app.jobs.tasks.maintenance.cleanup_expired_jobs",
        "schedule": 3600.0,
    },
}

celery_app.autodiscover_tasks([
    "app.jobs.tasks.email",
    "app.jobs.tasks.notifications",
    "app.jobs.tasks.ai",
    "app.jobs.tasks.reports",
    "app.jobs.tasks.webhooks",
    "app.jobs.tasks.backup",
    "app.jobs.tasks.maintenance",
])
