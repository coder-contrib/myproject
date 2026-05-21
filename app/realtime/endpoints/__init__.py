from app.realtime.endpoints.notifications import router as notifications_router
from app.realtime.endpoints.pos import router as pos_router
from app.realtime.endpoints.dashboard import router as dashboard_router

__all__ = ["notifications_router", "pos_router", "dashboard_router"]
