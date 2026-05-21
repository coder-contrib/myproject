import uuid
import traceback
import logging
from typing import Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
from collections import deque

from app.monitoring.config import monitoring_config

logger = logging.getLogger("monitoring.errors")


@dataclass
class ErrorEvent:
    id: str
    timestamp: str
    error_type: str
    message: str
    traceback_str: str
    module: str
    function: str
    line: int
    request_id: Optional[str] = None
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    path: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    context: dict = field(default_factory=dict)
    fingerprint: str = ""
    count: int = 1


class ErrorTracker:
    """Tracks and aggregates application errors."""

    def __init__(self, max_events: int = 1000):
        self._events: deque[ErrorEvent] = deque(maxlen=max_events)
        self._error_counts: dict[str, int] = {}
        self._fingerprints: dict[str, ErrorEvent] = {}

    def capture_exception(
        self,
        exc: Exception,
        request_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        path: Optional[str] = None,
        method: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> str:
        """Capture and track an exception."""
        if not monitoring_config.error_tracking_enabled:
            return ""

        tb = traceback.extract_tb(exc.__traceback__)
        last_frame = tb[-1] if tb else None

        event = ErrorEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            error_type=type(exc).__name__,
            message=str(exc),
            traceback_str=traceback.format_exception(type(exc), exc, exc.__traceback__).__str__(),
            module=last_frame.filename if last_frame else "unknown",
            function=last_frame.name if last_frame else "unknown",
            line=last_frame.lineno if last_frame else 0,
            request_id=request_id,
            tenant_id=tenant_id,
            user_id=user_id,
            path=path,
            method=method,
            context=context or {},
        )

        # Generate fingerprint for deduplication
        event.fingerprint = f"{event.error_type}:{event.module}:{event.function}:{event.line}"

        # Track counts
        self._error_counts[event.error_type] = self._error_counts.get(event.error_type, 0) + 1

        if event.fingerprint in self._fingerprints:
            self._fingerprints[event.fingerprint].count += 1
        else:
            self._fingerprints[event.fingerprint] = event

        self._events.append(event)

        logger.error(
            "Exception captured: %s: %s [fingerprint=%s]",
            event.error_type, event.message, event.fingerprint,
        )

        return event.id

    def get_recent_errors(self, limit: int = 50) -> list[dict]:
        events = list(self._events)[-limit:]
        events.reverse()
        return [
            {
                "id": e.id,
                "timestamp": e.timestamp,
                "type": e.error_type,
                "message": e.message,
                "module": e.module,
                "function": e.function,
                "line": e.line,
                "path": e.path,
                "method": e.method,
                "tenant_id": e.tenant_id,
                "fingerprint": e.fingerprint,
                "count": e.count,
            }
            for e in events
        ]

    def get_error_stats(self) -> dict:
        total = sum(self._error_counts.values())
        return {
            "total_errors": total,
            "unique_errors": len(self._fingerprints),
            "by_type": dict(sorted(
                self._error_counts.items(), key=lambda x: x[1], reverse=True
            )[:20]),
            "top_recurring": [
                {
                    "fingerprint": fp,
                    "type": event.error_type,
                    "message": event.message[:200],
                    "count": event.count,
                    "module": event.module,
                    "function": event.function,
                }
                for fp, event in sorted(
                    self._fingerprints.items(), key=lambda x: x[1].count, reverse=True
                )[:10]
            ],
        }

    def get_error_detail(self, error_id: str) -> Optional[dict]:
        for event in self._events:
            if event.id == error_id:
                return {
                    "id": event.id,
                    "timestamp": event.timestamp,
                    "type": event.error_type,
                    "message": event.message,
                    "traceback": event.traceback_str,
                    "module": event.module,
                    "function": event.function,
                    "line": event.line,
                    "path": event.path,
                    "method": event.method,
                    "request_id": event.request_id,
                    "tenant_id": event.tenant_id,
                    "user_id": event.user_id,
                    "context": event.context,
                    "fingerprint": event.fingerprint,
                }
        return None

    def clear(self):
        self._events.clear()
        self._error_counts.clear()
        self._fingerprints.clear()


error_tracker = ErrorTracker()
