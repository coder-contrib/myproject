from fastapi import APIRouter

from app.realtime.endpoints.notifications import router as notifications_router
from app.realtime.endpoints.pos import router as pos_router
from app.realtime.endpoints.dashboard import router as dashboard_router

realtime_router = APIRouter(tags=["realtime"])
realtime_router.include_router(notifications_router)
realtime_router.include_router(pos_router)
realtime_router.include_router(dashboard_router)
