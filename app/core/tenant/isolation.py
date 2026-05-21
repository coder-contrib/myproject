from uuid import UUID
from typing import TypeVar, Generic, Type, Sequence
from datetime import datetime, timezone
from sqlalchemy import select, func, Select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database.base_model import BaseModel
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

    async def get_by_id(self, id: UUID, include_deleted: bool = False) -> ModelType | None:
        query = select(self.model).where(self.model.id == id)
        if hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == self.ctx.tenant_id)
        if self.ctx.company_id and hasattr(self.model, "company_id"):
            query = query.where(self.model.company_id == self.ctx.company_id)
        if self.ctx.branch_id and hasattr(self.model, "branch_id"):
            query = query.where(self.model.branch_id == self.ctx.branch_id)
        if not include_deleted and hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at.is_(None))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id_strict(self, id: UUID) -> ModelType:
        instance = await self.get_by_id(id)
        if not instance:
            from app.core.exceptions.handlers import NotFoundException
            raise NotFoundException(self.model.__name__)
        return instance

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str | None = None,
        descending: bool = False,
        include_deleted: bool = False,
        **filters,
    ) -> Sequence[ModelType]:
        query = select(self.model)

        if hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == self.ctx.tenant_id)
        if self.ctx.company_id and hasattr(self.model, "company_id"):
            query = query.where(self.model.company_id == self.ctx.company_id)
        if self.ctx.branch_id and hasattr(self.model, "branch_id"):
            query = query.where(self.model.branch_id == self.ctx.branch_id)
        if not include_deleted and hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at.is_(None))

        for key, value in filters.items():
            if value is not None and hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        if order_by and hasattr(self.model, order_by):
            col = getattr(self.model, order_by)
            query = query.order_by(col.desc() if descending else col.asc())
        else:
            query = query.order_by(self.model.created_at.desc())

        result = await self.db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def count(self, include_deleted: bool = False, **filters) -> int:
        query = select(func.count(self.model.id))
        if hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == self.ctx.tenant_id)
        if self.ctx.company_id and hasattr(self.model, "company_id"):
            query = query.where(self.model.company_id == self.ctx.company_id)
        if self.ctx.branch_id and hasattr(self.model, "branch_id"):
            query = query.where(self.model.branch_id == self.ctx.branch_id)
        if not include_deleted and hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at.is_(None))

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

    async def bulk_create(self, items: list[dict]) -> list[ModelType]:
        instances = []
        for item in items:
            item["tenant_id"] = self.ctx.tenant_id
            if self.ctx.company_id and hasattr(self.model, "company_id") and "company_id" not in item:
                item["company_id"] = self.ctx.company_id
            if self.ctx.branch_id and hasattr(self.model, "branch_id") and "branch_id" not in item:
                item["branch_id"] = self.ctx.branch_id
            if self.ctx.user_id and hasattr(self.model, "created_by") and "created_by" not in item:
                item["created_by"] = self.ctx.user_id
            instances.append(self.model(**item))

        self.db.add_all(instances)
        await self.db.flush()
        for inst in instances:
            await self.db.refresh(inst)
        return instances

    async def update(self, id: UUID, expected_version: int | None = None, **kwargs) -> ModelType | None:
        instance = await self.get_by_id(id)
        if not instance:
            return None

        if expected_version is not None and hasattr(instance, "version"):
            if instance.version != expected_version:
                from app.shared.repository import OptimisticLockError
                raise OptimisticLockError(self.model.__name__)

        if self.ctx.user_id and hasattr(instance, "updated_by"):
            kwargs["updated_by"] = self.ctx.user_id

        if hasattr(instance, "version"):
            instance.version += 1

        if hasattr(instance, "updated_at"):
            instance.updated_at = datetime.now(timezone.utc)

        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update_strict(self, id: UUID, expected_version: int | None = None, **kwargs) -> ModelType:
        instance = await self.update(id, expected_version=expected_version, **kwargs)
        if not instance:
            from app.core.exceptions.handlers import NotFoundException
            raise NotFoundException(self.model.__name__)
        return instance

    async def soft_delete(self, id: UUID) -> bool:
        instance = await self.get_by_id(id)
        if not instance:
            return False

        if hasattr(instance, "deleted_at"):
            instance.deleted_at = datetime.now(timezone.utc)
            if self.ctx.user_id and hasattr(instance, "deleted_by"):
                instance.deleted_by = self.ctx.user_id
            await self.db.flush()
            return True
        return False

    async def restore(self, id: UUID) -> ModelType | None:
        instance = await self.get_by_id(id, include_deleted=True)
        if not instance:
            return None

        if hasattr(instance, "deleted_at"):
            instance.deleted_at = None
            if hasattr(instance, "deleted_by"):
                instance.deleted_by = None
            await self.db.flush()
            await self.db.refresh(instance)
            return instance
        return None

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

    async def find_many(self, ids: list[UUID]) -> Sequence[ModelType]:
        query = select(self.model).where(self.model.id.in_(ids))
        query = self._apply_tenant_filters(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    def query(self) -> Select:
        query = select(self.model)
        return self._apply_tenant_filters(query)
