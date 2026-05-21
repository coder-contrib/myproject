import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """Redirects HTTP to HTTPS in production. Respects X-Forwarded-Proto."""

    def __init__(self, app, force_https: bool | None = None):
        super().__init__(app)
        if force_https is not None:
            self.enabled = force_https
        else:
            self.enabled = os.getenv("FORCE_HTTPS", "false").lower() == "true"

    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)

        proto = request.headers.get("x-forwarded-proto", request.url.scheme)

        if proto == "http":
            url = request.url.replace(scheme="https")
            return RedirectResponse(url=str(url), status_code=301)

        return await call_next(request)
