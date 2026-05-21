import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_v1_router
from app.core.api.response import error_response
from app.core.security.cors import CORS_CONFIG
from app.core.middleware import (
    AuditLogMiddleware,
    RequestLoggingMiddleware,
    RateLimitMiddleware,
    InputSanitizationMiddleware,
    SecureHeadersMiddleware,
    HTTPSRedirectMiddleware,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

app = FastAPI(
    title="Ceramix AI ERP",
    version="1.0.0",
    description="Enterprise Resource Planning API - Multi-tenant SaaS",
    docs_url="/docs" if os.getenv("SHOW_DOCS", "true").lower() == "true" else None,
    redoc_url="/redoc" if os.getenv("SHOW_DOCS", "true").lower() == "true" else None,
)

# --- Middleware Stack (order matters: outermost first) ---

# HTTPS redirect (outermost - redirects before processing)
app.add_middleware(HTTPSRedirectMiddleware)

# Secure headers on every response
app.add_middleware(SecureHeadersMiddleware)

# CORS - must be before request processing
app.add_middleware(CORSMiddleware, **CORS_CONFIG)

# Request logging (timing + structured logs)
app.add_middleware(RequestLoggingMiddleware)

# Rate limiting (reject before heavy processing)
app.add_middleware(RateLimitMiddleware)

# Input sanitization (block XSS/SQLi payloads)
app.add_middleware(InputSanitizationMiddleware)

# Audit logging (innermost - has access to resolved state)
app.add_middleware(AuditLogMiddleware)


# --- Exception Handlers ---

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"field": ".".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=error_response(message="Validation failed", errors=errors),
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content=error_response(message="Resource not found"),
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content=error_response(message="Internal server error"),
    )


# --- Routes ---

app.include_router(api_v1_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
