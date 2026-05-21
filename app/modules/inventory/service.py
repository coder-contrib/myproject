from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.repository import BaseRepository
from app.modules.inventory.models import Product, Warehouse, Inventory, InventoryMovement, StockTransfer, ProductCategory


class InventoryService:
    def __init__(self, db: AsyncSession):
        self.product_repo = BaseRepository(Product, db)
        self.warehouse_repo = BaseRepository(Warehouse, db)
        self.inventory_repo = BaseRepository(Inventory, db)
        self.movement_repo = BaseRepository(InventoryMovement, db)
        self.transfer_repo = BaseRepository(StockTransfer, db)
        self.category_repo = BaseRepository(ProductCategory, db)
        self.db = db

    async def create_product(self, tenant_id: UUID, **kwargs) -> Product:
        return await self.product_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_products(self, tenant_id: UUID) -> list:
        return await self.product_repo.get_all(tenant_id=tenant_id)

    async def get_product(self, product_id: UUID) -> Product | None:
        return await self.product_repo.get_by_id(product_id)

    async def update_product(self, product_id: UUID, **kwargs) -> Product | None:
        return await self.product_repo.update(product_id, **kwargs)

    async def create_warehouse(self, tenant_id: UUID, **kwargs) -> Warehouse:
        return await self.warehouse_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_warehouses(self, tenant_id: UUID) -> list:
        return await self.warehouse_repo.get_all(tenant_id=tenant_id)

    async def create_movement(self, tenant_id: UUID, **kwargs) -> InventoryMovement:
        return await self.movement_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_movements(self, tenant_id: UUID) -> list:
        return await self.movement_repo.get_all(tenant_id=tenant_id)

    async def create_transfer(self, tenant_id: UUID, **kwargs) -> StockTransfer:
        return await self.transfer_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_transfers(self, tenant_id: UUID) -> list:
        return await self.transfer_repo.get_all(tenant_id=tenant_id)
