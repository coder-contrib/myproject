from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.core.middleware.tenant import TenantMiddleware, TenantValidationMiddleware, RequestLoggingMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    from app.core.database import engine
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TenantMiddleware)
app.add_middleware(TenantValidationMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Routers
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.tenants.router import router as tenants_router
from app.modules.crm.router import router as crm_router
from app.modules.inventory.router import router as inventory_router
from app.modules.sales.router import router as sales_router
from app.modules.purchases.router import router as purchases_router
from app.modules.accounting.router import router as accounting_router
from app.modules.treasury.router import router as treasury_router
from app.modules.hr.router import router as hr_router
from app.modules.manufacturing.router import router as manufacturing_router
from app.modules.ai.router import router as ai_router
from app.modules.notifications.router import router as notifications_router
from app.modules.reports.router import router as reports_router
from app.websocket.router import router as ws_router

app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(tenants_router, prefix="/api/v1")
app.include_router(crm_router, prefix="/api/v1")
app.include_router(inventory_router, prefix="/api/v1")
app.include_router(sales_router, prefix="/api/v1")
app.include_router(purchases_router, prefix="/api/v1")
app.include_router(accounting_router, prefix="/api/v1")
app.include_router(treasury_router, prefix="/api/v1")
app.include_router(hr_router, prefix="/api/v1")
app.include_router(manufacturing_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(ws_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}
