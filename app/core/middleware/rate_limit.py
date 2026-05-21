from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.security.rate_limiter import get_rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Applies token-bucket rate limiting per IP/user."""

    AUTH_PATHS = {"/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/refresh"}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path in self.AUTH_PATHS:
            limiter = get_rate_limiter("auth")
        else:
            limiter = get_rate_limiter("default")

        try:
            limiter.check(request)
        except Exception as exc:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "Rate limit exceeded. Please slow down.",
                    "data": None,
                    "errors": None,
                    "meta": None,
                },
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)

        remaining = limiter.get_remaining(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Limit"] = "60"

        return response
