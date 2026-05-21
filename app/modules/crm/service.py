from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.repository import BaseRepository
from app.modules.crm.models import Customer, Supplier, Lead, Opportunity, Activity


class CRMService:
    def __init__(self, db: AsyncSession):
        self.customer_repo = BaseRepository(Customer, db)
        self.supplier_repo = BaseRepository(Supplier, db)
        self.lead_repo = BaseRepository(Lead, db)
        self.opportunity_repo = BaseRepository(Opportunity, db)
        self.activity_repo = BaseRepository(Activity, db)
        self.db = db

    async def create_customer(self, tenant_id: UUID, **kwargs) -> Customer:
        return await self.customer_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_customers(self, tenant_id: UUID) -> list:
        return await self.customer_repo.get_all(tenant_id=tenant_id)

    async def get_customer(self, customer_id: UUID) -> Customer | None:
        return await self.customer_repo.get_by_id(customer_id)

    async def update_customer(self, customer_id: UUID, **kwargs) -> Customer | None:
        return await self.customer_repo.update(customer_id, **kwargs)

    async def delete_customer(self, customer_id: UUID, deleted_by: UUID) -> bool:
        return await self.customer_repo.soft_delete(customer_id, deleted_by=deleted_by)

    async def create_supplier(self, tenant_id: UUID, **kwargs) -> Supplier:
        return await self.supplier_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_suppliers(self, tenant_id: UUID) -> list:
        return await self.supplier_repo.get_all(tenant_id=tenant_id)

    async def create_lead(self, tenant_id: UUID, **kwargs) -> Lead:
        return await self.lead_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_leads(self, tenant_id: UUID) -> list:
        return await self.lead_repo.get_all(tenant_id=tenant_id)

    async def create_opportunity(self, tenant_id: UUID, **kwargs) -> Opportunity:
        return await self.opportunity_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_opportunities(self, tenant_id: UUID) -> list:
        return await self.opportunity_repo.get_all(tenant_id=tenant_id)
