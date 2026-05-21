from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.products import router as products_router
from app.api.v1.inventory import router as inventory_router
from app.api.v1.sales import router as sales_router
from app.api.v1.purchases import router as purchases_router
from app.api.v1.accounting import router as accounting_router
from app.api.v1.ai import router as ai_router
from app.api.v1.files import router as files_router
from app.api.v1.reports import router as reports_router
from app.api.v1.webhooks import router as webhooks_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(products_router)
api_v1_router.include_router(inventory_router)
api_v1_router.include_router(sales_router)
api_v1_router.include_router(purchases_router)
api_v1_router.include_router(accounting_router)
api_v1_router.include_router(ai_router)
api_v1_router.include_router(files_router)
api_v1_router.include_router(reports_router)
api_v1_router.include_router(webhooks_router)
