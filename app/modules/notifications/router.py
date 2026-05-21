from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user, get_current_tenant_id
from app.modules.notifications.schemas import *
from app.modules.notifications.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.post("/", response_model=NotificationResponse)
async def create_notification(data: NotificationCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await NotificationService(db).create(tenant_id=tenant_id, **data.model_dump())

@router.get("/", response_model=list[NotificationResponse])
async def list_notifications(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await NotificationService(db).get_user_notifications(user_id=current_user.id)

@router.patch("/{notification_id}/read")
async def mark_read(notification_id: UUID, db: AsyncSession = Depends(get_db)):
    await NotificationService(db).mark_read(notification_id)
    return {"detail": "Marked as read"}

@router.post("/read-all")
async def mark_all_read(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    count = await NotificationService(db).mark_all_read(user_id=current_user.id)
    return {"detail": f"{count} notifications marked as read"}
