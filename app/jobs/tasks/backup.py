import os
import subprocess
import logging
from datetime import datetime, timezone

from app.jobs.celery_app import celery_app
from app.jobs.base import BaseTask

logger = logging.getLogger("jobs.backup")

BACKUP_DIR = os.getenv("BACKUP_DIR", "/var/backups/ceramix")
DATABASE_URL = os.getenv("DATABASE_URL", "")


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="app.jobs.tasks.backup.run_daily_backup",
    soft_time_limit=1800,
    time_limit=3600,
)
def run_daily_backup(self):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"ceramix_backup_{timestamp}.sql.gz"
    filepath = os.path.join(BACKUP_DIR, filename)

    os.makedirs(BACKUP_DIR, exist_ok=True)

    backup_id = _create_backup_record(filename, filepath)

    try:
        db_params = _parse_database_url(DATABASE_URL)

        env = os.environ.copy()
        env["PGPASSWORD"] = db_params["password"]

        cmd = (
            f"pg_dump -h {db_params['host']} -p {db_params['port']} "
            f"-U {db_params['user']} -d {db_params['dbname']} "
            f"--format=custom --compress=9 -f {filepath}"
        )

        result = subprocess.run(
            cmd,
            shell=True,
            env=env,
            capture_output=True,
            text=True,
            timeout=1800,
        )

        if result.returncode != 0:
            raise Exception(f"pg_dump failed: {result.stderr}")

        file_size = os.path.getsize(filepath)
        _update_backup_record(backup_id, "completed", file_size)

        _cleanup_old_backups(keep_days=30)

        logger.info("Backup completed: %s (%d bytes)", filename, file_size)
        return {"file": filename, "size_bytes": file_size, "status": "completed"}

    except Exception as e:
        _update_backup_record(backup_id, "failed", 0)
        logger.error("Backup failed: %s", str(e))
        raise


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="app.jobs.tasks.backup.run_tenant_backup",
    soft_time_limit=600,
    time_limit=1200,
)
def run_tenant_backup(self, tenant_id: str):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"tenant_{tenant_id}_{timestamp}.sql.gz"
    filepath = os.path.join(BACKUP_DIR, "tenants", filename)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    db_params = _parse_database_url(DATABASE_URL)
    env = os.environ.copy()
    env["PGPASSWORD"] = db_params["password"]

    tables = [
        "companies", "branches", "users", "customers", "suppliers",
        "products", "warehouses", "inventory", "sales_invoices", "sales_items",
        "purchase_invoices", "purchase_items", "payments", "accounts",
        "journal_entries", "journal_entry_lines",
    ]

    table_args = " ".join(f"-t {t}" for t in tables)

    cmd = (
        f"pg_dump -h {db_params['host']} -p {db_params['port']} "
        f"-U {db_params['user']} -d {db_params['dbname']} "
        f"{table_args} --format=custom --compress=9 -f {filepath}"
    )

    result = subprocess.run(
        cmd,
        shell=True,
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )

    if result.returncode != 0:
        raise Exception(f"Tenant backup failed: {result.stderr}")

    file_size = os.path.getsize(filepath)
    logger.info("Tenant backup completed: %s (%d bytes)", filename, file_size)
    return {"file": filename, "size_bytes": file_size, "tenant_id": tenant_id}


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="app.jobs.tasks.backup.restore_backup",
    soft_time_limit=3600,
    time_limit=7200,
)
def restore_backup(self, backup_file: str):
    filepath = os.path.join(BACKUP_DIR, backup_file)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Backup file not found: {filepath}")

    db_params = _parse_database_url(DATABASE_URL)
    env = os.environ.copy()
    env["PGPASSWORD"] = db_params["password"]

    cmd = (
        f"pg_restore -h {db_params['host']} -p {db_params['port']} "
        f"-U {db_params['user']} -d {db_params['dbname']} "
        f"--clean --if-exists {filepath}"
    )

    result = subprocess.run(
        cmd,
        shell=True,
        env=env,
        capture_output=True,
        text=True,
        timeout=3600,
    )

    if result.returncode != 0:
        logger.warning("Restore warnings: %s", result.stderr[:500])

    logger.info("Restore completed from: %s", backup_file)
    return {"file": backup_file, "status": "restored"}


def _parse_database_url(url: str) -> dict:
    from urllib.parse import urlparse
    parsed = urlparse(url or "postgresql://postgres:postgres@localhost:5432/ceramix")
    return {
        "host": parsed.hostname or "localhost",
        "port": str(parsed.port or 5432),
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "dbname": parsed.path.lstrip("/") or "ceramix",
    }


def _create_backup_record(filename: str, filepath: str) -> str | None:
    try:
        from app.core.database import get_sync_engine
        from sqlalchemy import text

        engine = get_sync_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "INSERT INTO backup_logs (backup_type, file_path, status, started_at) "
                    "VALUES ('full', :path, 'running', NOW()) RETURNING id"
                ),
                {"path": filepath},
            )
            conn.commit()
            row = result.fetchone()
            return str(row[0]) if row else None
    except Exception:
        return None


def _update_backup_record(backup_id: str | None, status: str, size_bytes: int):
    if not backup_id:
        return
    try:
        from app.core.database import get_sync_engine
        from sqlalchemy import text

        engine = get_sync_engine()
        with engine.connect() as conn:
            conn.execute(
                text(
                    "UPDATE backup_logs SET status = :status, size_bytes = :size, "
                    "completed_at = NOW() WHERE id = :bid"
                ),
                {"status": status, "size": size_bytes, "bid": backup_id},
            )
            conn.commit()
    except Exception:
        pass


def _cleanup_old_backups(keep_days: int = 30):
    import glob
    from datetime import timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(days=keep_days)
    pattern = os.path.join(BACKUP_DIR, "ceramix_backup_*.sql.gz")

    for filepath in glob.glob(pattern):
        mtime = datetime.fromtimestamp(os.path.getmtime(filepath), tz=timezone.utc)
        if mtime < cutoff:
            os.remove(filepath)
            logger.info("Removed old backup: %s", filepath)
