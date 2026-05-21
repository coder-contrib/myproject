import time
import uuid
import json
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy import text

logger = logging.getLogger("audit")


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Logs all API requests to the api_audit_logs table."""

    SKIP_PATHS = {"/health", "/docs", "/openapi.json", "/redoc", "/favicon.ico"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        start_time = time.monotonic()
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        body = None
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                raw = await request.body()
                if raw and len(raw) < 10000:
                    body = json.loads(raw)
                    self._mask_sensitive(body)
            except Exception:
                body = None

        response = await call_next(request)

        latency_ms = int((time.monotonic() - start_time) * 1000)

        tenant_id = getattr(request.state, "tenant_id", None)
        user_id = getattr(request.state, "user_id", None)
        ip = self._get_client_ip(request)

        log_entry = {
            "request_id": request_id,
            "tenant_id": str(tenant_id) if tenant_id else None,
            "user_id": str(user_id) if user_id else None,
            "method": request.method,
            "endpoint": request.url.path,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
            "ip_address": ip,
        }

        logger.info(json.dumps(log_entry))

        try:
            db = getattr(request.state, "db", None)
            if db and tenant_id:
                await db.execute(
                    text(
                        "INSERT INTO api_audit_logs "
                        "(tenant_id, user_id, endpoint, method, request_body, response_code, latency_ms, ip_address) "
                        "VALUES (:tenant_id, :user_id, :endpoint, :method, :body, :code, :latency, :ip)"
                    ),
                    {
                        "tenant_id": tenant_id,
                        "user_id": user_id,
                        "endpoint": request.url.path,
                        "method": request.method,
                        "body": json.dumps(body) if body else None,
                        "code": response.status_code,
                        "latency": latency_ms,
                        "ip": ip,
                    },
                )
        except Exception as e:
            logger.warning(f"Failed to write audit log to DB: {e}")

        response.headers["X-Request-ID"] = request_id
        return response

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _mask_sensitive(self, data: dict) -> None:
        sensitive_keys = {"password", "password_hash", "secret", "token", "api_key", "credit_card"}
        for key in list(data.keys()):
            if key.lower() in sensitive_keys:
                data[key] = "***REDACTED***"
            elif isinstance(data[key], dict):
                self._mask_sensitive(data[key])
