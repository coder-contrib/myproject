from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.repository import BaseRepository
from app.modules.manufacturing.models import BillOfMaterials, ProductionOrder


class ManufacturingService:
    def __init__(self, db: AsyncSession):
        self.bom_repo = BaseRepository(BillOfMaterials, db)
        self.order_repo = BaseRepository(ProductionOrder, db)
        self.db = db

    async def create_bom(self, tenant_id: UUID, **kwargs) -> BillOfMaterials:
        return await self.bom_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_boms(self, tenant_id: UUID) -> list:
        return await self.bom_repo.get_all(tenant_id=tenant_id)

    async def create_production_order(self, tenant_id: UUID, **kwargs) -> ProductionOrder:
        return await self.order_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_production_orders(self, tenant_id: UUID) -> list:
        return await self.order_repo.get_all(tenant_id=tenant_id)

    async def update_order_status(self, order_id: UUID, status: str) -> ProductionOrder | None:
        return await self.order_repo.update(order_id, status=status)
