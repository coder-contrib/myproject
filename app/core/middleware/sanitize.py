import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.security.sanitizer import sanitize_input, contains_xss, contains_sql_injection


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """Sanitizes request bodies and rejects malicious payloads."""

    SKIP_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    body = await request.body()
                    if body:
                        data = json.loads(body)
                        threat = self._scan_for_threats(data)
                        if threat:
                            return JSONResponse(
                                status_code=400,
                                content={
                                    "success": False,
                                    "message": f"Request rejected: {threat}",
                                    "data": None,
                                    "errors": [{"field": "body", "message": threat}],
                                    "meta": None,
                                },
                            )
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass

        for param_value in request.query_params.values():
            if contains_sql_injection(param_value):
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "message": "Potentially malicious query parameter detected",
                        "data": None,
                        "errors": None,
                        "meta": None,
                    },
                )

        return await call_next(request)

    def _scan_for_threats(self, data, path="") -> str | None:
        if isinstance(data, str):
            if contains_xss(data):
                return f"XSS attempt detected in field '{path}'"
            if contains_sql_injection(data) and len(data) > 50:
                return f"SQL injection attempt detected in field '{path}'"
        elif isinstance(data, dict):
            for key, value in data.items():
                result = self._scan_for_threats(value, f"{path}.{key}" if path else key)
                if result:
                    return result
        elif isinstance(data, list):
            for i, item in enumerate(data):
                result = self._scan_for_threats(item, f"{path}[{i}]")
                if result:
                    return result
        return None
