import os
import logging
from contextlib import asynccontextmanager
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
from app.realtime.router import realtime_router
from app.realtime.redis_pubsub import RedisPubSub
from app.monitoring.middleware import MetricsMiddleware, PerformanceMiddleware
from app.monitoring.structured_logging import configure_logging

configure_logging()

redis_pubsub = RedisPubSub()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_pubsub.connect()
    yield
    await redis_pubsub.disconnect()


app = FastAPI(
    title="Ceramix AI ERP",
    version="1.0.0",
    description="Enterprise Resource Planning API - Multi-tenant SaaS",
    docs_url="/docs" if os.getenv("SHOW_DOCS", "true").lower() == "true" else None,
    redoc_url="/redoc" if os.getenv("SHOW_DOCS", "true").lower() == "true" else None,
    lifespan=lifespan,
)

# --- Middleware Stack ---
# In Starlette, the LAST add_middleware call becomes the OUTERMOST middleware.
# CORS must be outermost so it handles OPTIONS preflight before anything else.

# Audit logging (innermost)
app.add_middleware(AuditLogMiddleware)

# Input sanitization
app.add_middleware(InputSanitizationMiddleware)

# Rate limiting
app.add_middleware(RateLimitMiddleware)

# Request logging
app.add_middleware(RequestLoggingMiddleware)

# Performance monitoring
app.add_middleware(PerformanceMiddleware)

# Prometheus metrics
app.add_middleware(MetricsMiddleware)

# HTTPS redirect
app.add_middleware(HTTPSRedirectMiddleware)

# Secure headers
app.add_middleware(SecureHeadersMiddleware)

# CORS - MUST be last (= outermost) to handle preflight OPTIONS requests
app.add_middleware(CORSMiddleware, **CORS_CONFIG)


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
app.include_router(realtime_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
