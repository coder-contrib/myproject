from uuid import UUID
from typing import TypeVar, Generic, Type, Sequence, Any
from sqlalchemy import select, and_, Select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import BaseModel
from app.core.tenant.context import TenantContext

ModelType = TypeVar("ModelType", bound=BaseModel)


class TenantIsolatedRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession, ctx: TenantContext):
        self.model = model
        self.db = db
        self.ctx = ctx

    def _apply_tenant_filters(self, query: Select) -> Select:
        if hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == self.ctx.tenant_id)

        if self.ctx.company_id and hasattr(self.model, "company_id"):
            query = query.where(self.model.company_id == self.ctx.company_id)

        if self.ctx.branch_id and hasattr(self.model, "branch_id"):
            query = query.where(self.model.branch_id == self.ctx.branch_id)

        if hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at.is_(None))

        return query

    async def get_by_id(self, id: UUID) -> ModelType | None:
        query = select(self.model).where(self.model.id == id)
        query = self._apply_tenant_filters(query)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id_strict(self, id: UUID) -> ModelType:
        instance = await self.get_by_id(id)
        if not instance:
            from app.core.exceptions.handlers import NotFoundException
            raise NotFoundException(self.model.__name__)
        return instance

    async def get_all(self, skip: int = 0, limit: int = 100, **filters) -> Sequence[ModelType]:
        query = select(self.model)
        query = self._apply_tenant_filters(query)

        for key, value in filters.items():
            if value is not None and hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        result = await self.db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def count(self, **filters) -> int:
        from sqlalchemy import func
        query = select(func.count(self.model.id))
        query = self._apply_tenant_filters(query)

        for key, value in filters.items():
            if value is not None and hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def create(self, **kwargs) -> ModelType:
        kwargs["tenant_id"] = self.ctx.tenant_id

        if self.ctx.company_id and hasattr(self.model, "company_id") and "company_id" not in kwargs:
            kwargs["company_id"] = self.ctx.company_id

        if self.ctx.branch_id and hasattr(self.model, "branch_id") and "branch_id" not in kwargs:
            kwargs["branch_id"] = self.ctx.branch_id

        if self.ctx.user_id and hasattr(self.model, "created_by") and "created_by" not in kwargs:
            kwargs["created_by"] = self.ctx.user_id

        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update(self, id: UUID, **kwargs) -> ModelType | None:
        instance = await self.get_by_id(id)
        if not instance:
            return None

        if self.ctx.user_id and hasattr(instance, "updated_by"):
            kwargs["updated_by"] = self.ctx.user_id

        if hasattr(instance, "version"):
            instance.version += 1

        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update_strict(self, id: UUID, **kwargs) -> ModelType:
        instance = await self.update(id, **kwargs)
        if not instance:
            from app.core.exceptions.handlers import NotFoundException
            raise NotFoundException(self.model.__name__)
        return instance

    async def soft_delete(self, id: UUID) -> bool:
        instance = await self.get_by_id(id)
        if not instance:
            return False

        if hasattr(instance, "deleted_at"):
            from datetime import datetime, timezone
            instance.deleted_at = datetime.now(timezone.utc)
            if self.ctx.user_id and hasattr(instance, "deleted_by"):
                instance.deleted_by = self.ctx.user_id
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

    async def exists(self, id: UUID) -> bool:
        return await self.get_by_id(id) is not None

    async def find_one(self, **filters) -> ModelType | None:
        query = select(self.model)
        query = self._apply_tenant_filters(query)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    def query(self) -> Select:
        query = select(self.model)
        return self._apply_tenant_filters(query)
