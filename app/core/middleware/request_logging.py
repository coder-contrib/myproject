import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("app.requests")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Structured request/response logging with timing."""

    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()

        ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if not ip:
            ip = request.client.host if request.client else "-"

        response = await call_next(request)

        duration_ms = int((time.monotonic() - start) * 1000)

        logger.info(
            "%s %s %s %dms %d",
            ip,
            request.method,
            request.url.path,
            duration_ms,
            response.status_code,
        )

        response.headers["X-Response-Time"] = f"{duration_ms}ms"
        return response
