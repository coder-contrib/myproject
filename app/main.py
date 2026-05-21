from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.api.v1 import api_v1_router
from app.core.api.response import error_response

app = FastAPI(
    title="Ceramix AI ERP",
    version="1.0.0",
    description="Enterprise Resource Planning API - Multi-tenant SaaS",
)


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


app.include_router(api_v1_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
