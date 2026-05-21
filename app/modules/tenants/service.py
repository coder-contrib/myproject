from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.repository import BaseRepository
from app.modules.tenants.models import Tenant, Company, Branch


class TenantService:
    def __init__(self, db: AsyncSession):
        self.repo = BaseRepository(Tenant, db)
        self.company_repo = BaseRepository(Company, db)
        self.branch_repo = BaseRepository(Branch, db)
        self.db = db

    async def create_tenant(self, name: str) -> Tenant:
        return await self.repo.create(name=name)

    async def get_tenant(self, tenant_id: UUID) -> Tenant | None:
        return await self.repo.get_by_id(tenant_id)

    async def create_company(self, tenant_id: UUID, **kwargs) -> Company:
        return await self.company_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_companies(self, tenant_id: UUID) -> list:
        return await self.company_repo.get_all(tenant_id=tenant_id)

    async def create_branch(self, tenant_id: UUID, **kwargs) -> Branch:
        return await self.branch_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_branches(self, tenant_id: UUID) -> list:
        return await self.branch_repo.get_all(tenant_id=tenant_id)
