from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_tenant_id
from app.modules.manufacturing.schemas import *
from app.modules.manufacturing.service import ManufacturingService

router = APIRouter(prefix="/manufacturing", tags=["manufacturing"])

@router.post("/bom", response_model=BOMResponse)
async def create_bom(data: BOMCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await ManufacturingService(db).create_bom(tenant_id=tenant_id, **data.model_dump())

@router.get("/bom", response_model=list[BOMResponse])
async def list_boms(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await ManufacturingService(db).get_boms(tenant_id)

@router.post("/orders", response_model=ProductionOrderResponse)
async def create_order(data: ProductionOrderCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await ManufacturingService(db).create_production_order(tenant_id=tenant_id, **data.model_dump())

@router.get("/orders", response_model=list[ProductionOrderResponse])
async def list_orders(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await ManufacturingService(db).get_production_orders(tenant_id)

@router.patch("/orders/{order_id}/status")
async def update_status(order_id: UUID, status: str, db: AsyncSession = Depends(get_db)):
    result = await ManufacturingService(db).update_order_status(order_id, status)
    return {"id": str(result.id), "status": result.status}
