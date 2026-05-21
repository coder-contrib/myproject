from uuid import UUID
from typing import TypeVar, Generic, Type, Sequence, Any
from datetime import datetime, timezone
from sqlalchemy import select, update, func, and_, event
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database.base_model import BaseModel
from app.core.exceptions.handlers import NotFoundException, AppException

ModelType = TypeVar("ModelType", bound=BaseModel)


class OptimisticLockError(AppException):
    def __init__(self, model_name: str):
        super().__init__(
            f"{model_name} was modified by another user. Please refresh and try again.",
            status_code=409,
        )


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    def _base_query(self):
        query = select(self.model)
        if hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at.is_(None))
        return query

    async def get_by_id(self, id: UUID, include_deleted: bool = False) -> ModelType | None:
        query = select(self.model).where(self.model.id == id)
        if not include_deleted and hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at.is_(None))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id_strict(self, id: UUID) -> ModelType:
        instance = await self.get_by_id(id)
        if not instance:
            raise NotFoundException(self.model.__name__)
        return instance

    async def get_all(
        self,
        tenant_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str | None = None,
        descending: bool = False,
        include_deleted: bool = False,
        **filters,
    ) -> Sequence[ModelType]:
        query = select(self.model)

        if tenant_id and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)

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

    async def count(self, tenant_id: UUID | None = None, include_deleted: bool = False, **filters) -> int:
        query = select(func.count(self.model.id))

        if tenant_id and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)

        if not include_deleted and hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at.is_(None))

        for key, value in filters.items():
            if value is not None and hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def exists(self, id: UUID) -> bool:
        return await self.get_by_id(id) is not None

    async def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def bulk_create(self, items: list[dict]) -> list[ModelType]:
        instances = [self.model(**item) for item in items]
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
                raise OptimisticLockError(self.model.__name__)

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
            raise NotFoundException(self.model.__name__)
        return instance

    async def soft_delete(self, id: UUID, deleted_by: UUID | None = None) -> bool:
        instance = await self.get_by_id(id)
        if not instance:
            return False

        if hasattr(instance, "deleted_at"):
            instance.deleted_at = datetime.now(timezone.utc)
            if deleted_by and hasattr(instance, "deleted_by"):
                instance.deleted_by = deleted_by
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
        instance = await self.get_by_id(id, include_deleted=True)
        if not instance:
            return False
        await self.db.delete(instance)
        await self.db.flush()
        return True

    async def find_one(self, **filters) -> ModelType | None:
        query = self._base_query()
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def find_many(self, ids: list[UUID]) -> Sequence[ModelType]:
        query = self._base_query().where(self.model.id.in_(ids))
        result = await self.db.execute(query)
        return result.scalars().all()
