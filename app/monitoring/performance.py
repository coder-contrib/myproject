import time
import logging
from typing import Optional
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.monitoring.config import monitoring_config

logger = logging.getLogger("monitoring.performance")


@dataclass
class RequestTiming:
    path: str
    method: str
    status_code: int
    duration_ms: float
    timestamp: str
    tenant_id: Optional[str] = None
    request_id: Optional[str] = None


class PerformanceMonitor:
    """Tracks request performance and identifies slow endpoints."""

    def __init__(self, max_history: int = 5000):
        self._history: deque[RequestTiming] = deque(maxlen=max_history)
        self._endpoint_stats: dict[str, dict] = defaultdict(lambda: {
            "count": 0,
            "total_ms": 0.0,
            "min_ms": float("inf"),
            "max_ms": 0.0,
            "slow_count": 0,
            "error_count": 0,
        })
        self._active_requests: dict[str, float] = {}

    def start_request(self, request_id: str):
        self._active_requests[request_id] = time.time()

    def end_request(
        self,
        request_id: str,
        path: str,
        method: str,
        status_code: int,
        tenant_id: Optional[str] = None,
    ) -> float:
        start_time = self._active_requests.pop(request_id, None)
        if start_time is None:
            return 0.0

        duration_ms = (time.time() - start_time) * 1000

        timing = RequestTiming(
            path=path,
            method=method,
            status_code=status_code,
            duration_ms=round(duration_ms, 2),
            timestamp=datetime.now(timezone.utc).isoformat(),
            tenant_id=tenant_id,
            request_id=request_id,
        )
        self._history.append(timing)

        # Update stats
        endpoint_key = f"{method} {path}"
        stats = self._endpoint_stats[endpoint_key]
        stats["count"] += 1
        stats["total_ms"] += duration_ms
        stats["min_ms"] = min(stats["min_ms"], duration_ms)
        stats["max_ms"] = max(stats["max_ms"], duration_ms)

        if status_code >= 500:
            stats["error_count"] += 1

        if duration_ms >= monitoring_config.performance_slow_threshold_ms:
            stats["slow_count"] += 1
            logger.warning(
                "Slow request: %s %s took %.1fms (threshold: %dms)",
                method, path, duration_ms, monitoring_config.performance_slow_threshold_ms,
            )

        return duration_ms

    def get_endpoint_stats(self, top_n: int = 20) -> list[dict]:
        results = []
        for endpoint, stats in self._endpoint_stats.items():
            count = stats["count"]
            if count == 0:
                continue
            results.append({
                "endpoint": endpoint,
                "request_count": count,
                "avg_ms": round(stats["total_ms"] / count, 2),
                "min_ms": round(stats["min_ms"], 2) if stats["min_ms"] != float("inf") else 0,
                "max_ms": round(stats["max_ms"], 2),
                "slow_count": stats["slow_count"],
                "error_count": stats["error_count"],
                "error_rate": round(stats["error_count"] / count * 100, 1),
            })

        results.sort(key=lambda x: x["avg_ms"], reverse=True)
        return results[:top_n]

    def get_slow_requests(self, limit: int = 50) -> list[dict]:
        threshold = monitoring_config.performance_slow_threshold_ms
        slow = [
            {
                "path": t.path,
                "method": t.method,
                "duration_ms": t.duration_ms,
                "status_code": t.status_code,
                "timestamp": t.timestamp,
                "tenant_id": t.tenant_id,
            }
            for t in self._history
            if t.duration_ms >= threshold
        ]
        slow.sort(key=lambda x: x["duration_ms"], reverse=True)
        return slow[:limit]

    def get_overview(self) -> dict:
        if not self._history:
            return {"total_requests": 0}

        total = len(self._history)
        durations = [t.duration_ms for t in self._history]
        errors = sum(1 for t in self._history if t.status_code >= 500)
        slow = sum(1 for t in self._history if t.duration_ms >= monitoring_config.performance_slow_threshold_ms)

        sorted_durations = sorted(durations)
        p50 = sorted_durations[int(total * 0.5)] if total > 0 else 0
        p95 = sorted_durations[int(total * 0.95)] if total > 0 else 0
        p99 = sorted_durations[int(total * 0.99)] if total > 0 else 0

        return {
            "total_requests": total,
            "avg_duration_ms": round(sum(durations) / total, 2),
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "p99_ms": round(p99, 2),
            "min_ms": round(min(durations), 2),
            "max_ms": round(max(durations), 2),
            "error_count": errors,
            "error_rate_pct": round(errors / total * 100, 2),
            "slow_count": slow,
            "slow_rate_pct": round(slow / total * 100, 2),
            "active_requests": len(self._active_requests),
            "slow_threshold_ms": monitoring_config.performance_slow_threshold_ms,
        }

    def get_throughput(self, window_minutes: int = 5) -> dict:
        """Calculate requests per minute over a rolling window."""
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        cutoff_str = cutoff.isoformat()

        recent = [t for t in self._history if t.timestamp >= cutoff_str]
        rpm = len(recent) / window_minutes if window_minutes > 0 else 0

        return {
            "window_minutes": window_minutes,
            "total_requests": len(recent),
            "requests_per_minute": round(rpm, 1),
        }


perf_monitor = PerformanceMonitor()
