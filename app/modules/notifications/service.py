from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.repository import BaseRepository
from app.modules.notifications.models import Notification


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.repo = BaseRepository(Notification, db)
        self.db = db

    async def create(self, tenant_id: UUID, **kwargs) -> Notification:
        return await self.repo.create(tenant_id=tenant_id, **kwargs)

    async def get_user_notifications(self, user_id: UUID) -> list:
        result = await self.db.execute(
            select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc()).limit(50)
        )
        return result.scalars().all()

    async def mark_read(self, notification_id: UUID) -> Notification | None:
        return await self.repo.update(notification_id, is_read=True)

    async def mark_all_read(self, user_id: UUID) -> int:
        result = await self.db.execute(
            update(Notification).where(Notification.user_id == user_id, Notification.is_read == False).values(is_read=True)
        )
        return result.rowcount
