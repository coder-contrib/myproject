from uuid import UUID
from typing import TypeVar, Generic, Type, Sequence
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: UUID) -> ModelType | None:
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_all(
        self, tenant_id: UUID | None = None, skip: int = 0, limit: int = 100
    ) -> Sequence[ModelType]:
        query = select(self.model)
        if tenant_id and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)
        if hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at.is_(None))
        result = await self.db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update(self, id: UUID, **kwargs) -> ModelType | None:
        instance = await self.get_by_id(id)
        if not instance:
            return None
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def soft_delete(self, id: UUID, deleted_by: UUID | None = None) -> bool:
        instance = await self.get_by_id(id)
        if not instance:
            return False
        if hasattr(instance, "deleted_at"):
            from datetime import datetime
            instance.deleted_at = datetime.utcnow()
            if deleted_by and hasattr(instance, "deleted_by"):
                instance.deleted_by = deleted_by
            await self.db.flush()
            return True
        return False

    async def hard_delete(self, id: UUID) -> bool:
        instance = await self.get_by_id(id)
        if not instance:
            return False
        await self.db.delete(instance)
        await self.db.flush()
        return True
