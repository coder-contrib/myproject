from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_tenant_id
from app.modules.inventory.schemas import *
from app.modules.inventory.service import InventoryService

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/products", response_model=ProductResponse)
async def create_product(data: ProductCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await InventoryService(db).create_product(tenant_id=tenant_id, **data.model_dump())

@router.get("/products", response_model=list[ProductResponse])
async def list_products(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await InventoryService(db).get_products(tenant_id)

@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: UUID, db: AsyncSession = Depends(get_db)):
    return await InventoryService(db).get_product(product_id)

@router.post("/warehouses", response_model=WarehouseResponse)
async def create_warehouse(data: WarehouseCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await InventoryService(db).create_warehouse(tenant_id=tenant_id, **data.model_dump())

@router.get("/warehouses", response_model=list[WarehouseResponse])
async def list_warehouses(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await InventoryService(db).get_warehouses(tenant_id)

@router.post("/movements", response_model=MovementResponse)
async def create_movement(data: MovementCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await InventoryService(db).create_movement(tenant_id=tenant_id, **data.model_dump())

@router.get("/movements", response_model=list[MovementResponse])
async def list_movements(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await InventoryService(db).get_movements(tenant_id)

@router.post("/transfers", response_model=StockTransferResponse)
async def create_transfer(data: StockTransferCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await InventoryService(db).create_transfer(tenant_id=tenant_id, **data.model_dump())

@router.get("/transfers", response_model=list[StockTransferResponse])
async def list_transfers(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await InventoryService(db).get_transfers(tenant_id)
