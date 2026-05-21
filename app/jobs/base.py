import logging
import traceback
from celery import Task
from app.jobs.celery_app import celery_app

logger = logging.getLogger("jobs")


class BaseTask(Task):
    """Base task with automatic retry, error logging, and job status tracking."""

    abstract = True
    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True
    max_retries = 3

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(
            "Task %s[%s] failed: %s\n%s",
            self.name,
            task_id,
            str(exc),
            traceback.format_exc(),
        )
        self._update_job_status(task_id, "failed", error_message=str(exc))

    def on_success(self, retval, task_id, args, kwargs):
        logger.info("Task %s[%s] completed successfully", self.name, task_id)
        self._update_job_status(task_id, "completed")

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.warning(
            "Task %s[%s] retrying (%d/%d): %s",
            self.name,
            task_id,
            self.request.retries,
            self.max_retries,
            str(exc),
        )

    def before_start(self, task_id, args, kwargs):
        logger.info("Task %s[%s] starting", self.name, task_id)
        self._update_job_status(task_id, "running")

    def _update_job_status(self, task_id: str, status: str, error_message: str | None = None):
        try:
            from app.jobs.job_tracker import update_job_status
            update_job_status(task_id, status, error_message)
        except Exception:
            pass
