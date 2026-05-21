import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

PUBLIC_PATHS = {"/health", "/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/refresh",
                "/api/v1/auth/password-reset/request", "/api/v1/auth/password-reset/confirm", "/docs",
                "/redoc", "/openapi.json"}


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.tenant_id = None
        request.state.company_id = None
        request.state.branch_id = None
        request.state.user_id = None

        if request.url.path in PUBLIC_PATHS or request.url.path.startswith("/docs"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

                if payload.get("tenant_id"):
                    request.state.tenant_id = uuid.UUID(payload["tenant_id"])
                if payload.get("sub"):
                    request.state.user_id = uuid.UUID(payload["sub"])
                if payload.get("company_id"):
                    request.state.company_id = uuid.UUID(payload["company_id"])
                if payload.get("branch_id"):
                    request.state.branch_id = uuid.UUID(payload["branch_id"])
            except (JWTError, ValueError, KeyError):
                pass

        header_company = request.headers.get("X-Company-ID")
        header_branch = request.headers.get("X-Branch-ID")

        if header_company and not request.state.company_id:
            try:
                request.state.company_id = uuid.UUID(header_company)
            except ValueError:
                return Response(
                    content='{"detail":"Invalid X-Company-ID header format"}',
                    status_code=400,
                    media_type="application/json",
                )

        if header_branch and not request.state.branch_id:
            try:
                request.state.branch_id = uuid.UUID(header_branch)
            except ValueError:
                return Response(
                    content='{"detail":"Invalid X-Branch-ID header format"}',
                    status_code=400,
                    media_type="application/json",
                )

        response = await call_next(request)
        return response


class TenantValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in PUBLIC_PATHS or request.url.path.startswith("/docs"):
            return await call_next(request)

        tenant_id = getattr(request.state, "tenant_id", None)
        company_id = getattr(request.state, "company_id", None)
        branch_id = getattr(request.state, "branch_id", None)

        if company_id and not tenant_id:
            return Response(
                content='{"detail":"Company context requires tenant context"}',
                status_code=400,
                media_type="application/json",
            )

        if branch_id and not company_id:
            return Response(
                content='{"detail":"Branch context requires company context"}',
                status_code=400,
                media_type="application/json",
            )

        response = await call_next(request)
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()

        request.state.request_id = request_id

        response: Response = await call_next(request)

        duration_ms = int((time.time() - start_time) * 1000)

        tenant_id = getattr(request.state, "tenant_id", None)
        logger.info(
            f"{request.method} {request.url.path} "
            f"status={response.status_code} "
            f"duration={duration_ms}ms "
            f"request_id={request_id} "
            f"tenant_id={tenant_id}"
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms}ms"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_client=None, requests_per_minute: int = 60):
        super().__init__(app)
        self.redis = redis_client
        self.rpm = requests_per_minute

    async def dispatch(self, request: Request, call_next):
        if not self.redis:
            return await call_next(request)

        tenant_id = getattr(request.state, "tenant_id", None)
        if tenant_id:
            key = f"rate_limit:tenant:{tenant_id}"
        else:
            client_ip = request.client.host if request.client else "unknown"
            key = f"rate_limit:ip:{client_ip}"

        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, 60)

        if current > self.rpm:
            return Response(
                content='{"detail":"Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.rpm - current))
        return response
