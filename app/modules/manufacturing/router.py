from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.tenant import TenantContext, get_tenant_context
from app.modules.manufacturing.schemas import (
    BOMCreate, BOMResponse,
    ProductionOrderCreate, ProductionOrderResponse, ProductionOrderStatusUpdate,
    ConsumeMaterialRequest, MaterialConsumptionResponse,
)
from app.modules.manufacturing.service import ManufacturingService

router = APIRouter(prefix="/manufacturing", tags=["manufacturing"])


def _svc(db: AsyncSession, ctx: TenantContext) -> ManufacturingService:
    return ManufacturingService(db, ctx)


# --- Bill of Materials ---

@router.post("/bom", response_model=BOMResponse)
async def create_bom(data: BOMCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    items = [item.model_dump() for item in data.items]
    return await _svc(db, ctx).create_bom(
        product_id=data.product_id,
        name=data.name,
        notes=data.notes,
        items=items,
    )


@router.get("/bom", response_model=list[BOMResponse])
async def list_boms(
    product_id: UUID | None = None,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db, ctx).get_boms(product_id=product_id)


@router.get("/bom/{bom_id}", response_model=BOMResponse)
async def get_bom(bom_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_bom(bom_id)


# --- Production Orders ---

@router.post("/orders", response_model=ProductionOrderResponse)
async def create_production_order(data: ProductionOrderCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).create_production_order(**data.model_dump())


@router.get("/orders", response_model=list[ProductionOrderResponse])
async def list_production_orders(
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db, ctx).get_production_orders(skip=skip, limit=limit, status=status)


@router.get("/orders/{order_id}", response_model=ProductionOrderResponse)
async def get_production_order(order_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_production_order(order_id)


@router.patch("/orders/{order_id}/status", response_model=ProductionOrderResponse)
async def update_order_status(order_id: UUID, data: ProductionOrderStatusUpdate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).update_order_status(order_id, status=data.status, produced_quantity=data.produced_quantity)


# --- Material Consumption ---

@router.post("/orders/{order_id}/consume", response_model=MaterialConsumptionResponse)
async def consume_material(order_id: UUID, data: ConsumeMaterialRequest, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).consume_material(
        order_id=order_id,
        material_id=data.material_id,
        quantity=data.quantity,
        warehouse_id=data.warehouse_id,
    )
