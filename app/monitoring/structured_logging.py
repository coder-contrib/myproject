import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any
from logging.handlers import RotatingFileHandler

from app.monitoring.config import monitoring_config


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "tenant_id"):
            log_entry["tenant_id"] = record.tenant_id
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms
        if hasattr(record, "status_code"):
            log_entry["status_code"] = record.status_code
        if hasattr(record, "method"):
            log_entry["method"] = record.method
        if hasattr(record, "path"):
            log_entry["path"] = record.path

        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        return json.dumps(log_entry, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable structured text formatter."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        base = f"{timestamp} [{record.levelname:8s}] {record.name}: {record.getMessage()}"

        extras = []
        if hasattr(record, "request_id"):
            extras.append(f"req={record.request_id}")
        if hasattr(record, "tenant_id"):
            extras.append(f"tenant={record.tenant_id}")
        if hasattr(record, "duration_ms"):
            extras.append(f"duration={record.duration_ms}ms")
        if hasattr(record, "status_code"):
            extras.append(f"status={record.status_code}")

        if extras:
            base += f" | {' '.join(extras)}"

        if record.exc_info and record.exc_info[0]:
            base += f"\n{self.formatException(record.exc_info)}"

        return base


class StructuredLogger:
    """Enhanced logger with structured context injection."""

    def __init__(self, name: str):
        self._logger = logging.getLogger(name)
        self._context: dict = {}

    def bind(self, **kwargs) -> "StructuredLogger":
        """Create a child logger with additional context."""
        new_logger = StructuredLogger(self._logger.name)
        new_logger._context = {**self._context, **kwargs}
        return new_logger

    def _log(self, level: int, message: str, **kwargs):
        extra = {**self._context, **kwargs}
        record = self._logger.makeRecord(
            self._logger.name, level, "", 0, message, (), None
        )
        for key, value in extra.items():
            setattr(record, key, value)
        if "data" in kwargs:
            record.extra_data = kwargs["data"]
        self._logger.handle(record)

    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        self._log(logging.CRITICAL, message, **kwargs)

    def exception(self, message: str, **kwargs):
        self._logger.exception(message, extra={**self._context, **kwargs})


def get_logger(name: str) -> StructuredLogger:
    return StructuredLogger(name)


def configure_logging():
    """Configure the root logging with structured formatters."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, monitoring_config.log_level.upper(), logging.INFO))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Choose formatter
    if monitoring_config.log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    # Stdout handler
    if monitoring_config.log_output in ("stdout", "both"):
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        root_logger.addHandler(stdout_handler)

    # File handler
    if monitoring_config.log_output in ("file", "both"):
        log_path = Path(monitoring_config.log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            str(log_path),
            maxBytes=monitoring_config.log_max_size_mb * 1024 * 1024,
            backupCount=monitoring_config.log_backup_count,
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
