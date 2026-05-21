import uuid
import time
import logging
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.monitoring.metrics import metrics_collector
from app.monitoring.performance import perf_monitor
from app.monitoring.error_tracking import error_tracker

logger = logging.getLogger("monitoring.middleware")


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware that collects Prometheus-compatible metrics for every request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        method = request.method
        path = self._normalize_path(request.url.path)

        # Track in-flight
        in_progress = metrics_collector.gauge(
            "http_requests_in_progress", "In-flight HTTP requests", ["method"]
        )
        in_progress.inc(method=method)

        start = time.time()
        try:
            response = await call_next(request)
            status = str(response.status_code)
        except Exception as exc:
            status = "500"
            raise
        finally:
            duration_ms = (time.time() - start) * 1000
            in_progress.dec(method=method)

            # Record metrics
            counter = metrics_collector.counter(
                "http_requests_total", "Total HTTP requests", ["method", "path", "status"]
            )
            counter.inc(method=method, path=path, status=status)

            histogram = metrics_collector.histogram(
                "http_request_duration_ms", "HTTP request duration in ms", ["method", "path"]
            )
            histogram.observe(duration_ms, method=method, path=path)

        return response

    def _normalize_path(self, path: str) -> str:
        """Normalize path to reduce cardinality (replace UUIDs/IDs with :id)."""
        import re
        path = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            ":id", path
        )
        path = re.sub(r"/\d+", "/:id", path)
        return path


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware that tracks request performance and captures errors."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        tenant_id = request.headers.get("X-Tenant-ID")
        user_id = request.headers.get("X-User-ID")

        perf_monitor.start_request(request_id)

        try:
            response = await call_next(request)

            duration_ms = perf_monitor.end_request(
                request_id=request_id,
                path=request.url.path,
                method=request.method,
                status_code=response.status_code,
                tenant_id=tenant_id,
            )

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"

            return response

        except Exception as exc:
            perf_monitor.end_request(
                request_id=request_id,
                path=request.url.path,
                method=request.method,
                status_code=500,
                tenant_id=tenant_id,
            )

            error_tracker.capture_exception(
                exc=exc,
                request_id=request_id,
                tenant_id=tenant_id,
                user_id=user_id,
                path=request.url.path,
                method=request.method,
            )

            errors_counter = metrics_collector.counter(
                "errors_total", "Total application errors", ["type", "module"]
            )
            errors_counter.inc(type=type(exc).__name__, module="http")

            raise
