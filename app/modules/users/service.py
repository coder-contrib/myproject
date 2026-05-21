from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import hash_password
from app.core.exceptions.handlers import NotFoundException, DuplicateException
from app.shared.repository import BaseRepository
from app.modules.users.models import User, Role


class UserService:
    def __init__(self, db: AsyncSession):
        self.repo = BaseRepository(User, db)
        self.role_repo = BaseRepository(Role, db)
        self.db = db

    async def create_user(self, tenant_id: UUID, **kwargs) -> User:
        email = kwargs.get("email")
        existing = await self.db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise DuplicateException("User with this email")

        password = kwargs.pop("password")
        kwargs["password_hash"] = hash_password(password)
        return await self.repo.create(tenant_id=tenant_id, **kwargs)

    async def get_user(self, user_id: UUID) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User")
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def list_users(self, tenant_id: UUID) -> list:
        return await self.repo.get_all(tenant_id=tenant_id)

    async def update_user(self, user_id: UUID, **kwargs) -> User:
        user = await self.repo.update(user_id, **kwargs)
        if not user:
            raise NotFoundException("User")
        return user

    async def delete_user(self, user_id: UUID, deleted_by: UUID) -> bool:
        return await self.repo.soft_delete(user_id, deleted_by=deleted_by)

    async def create_role(self, tenant_id: UUID, **kwargs) -> Role:
        return await self.role_repo.create(tenant_id=tenant_id, **kwargs)

    async def list_roles(self, tenant_id: UUID) -> list:
        return await self.role_repo.get_all(tenant_id=tenant_id)
