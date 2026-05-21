from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.tenant import TenantContext, get_tenant_context
from app.modules.inventory.schemas import (
    CategoryCreate, CategoryUpdate, CategoryResponse,
    ProductCreate, ProductUpdate, ProductResponse,
    WarehouseCreate, WarehouseUpdate, WarehouseResponse,
    InventoryResponse, InventoryAdjustment,
    BatchCreate, BatchResponse,
    MovementCreate, MovementResponse,
    StockTransferCreate, StockTransferResponse, TransferStatusUpdate,
    StockAlertResponse,
)
from app.modules.inventory.service import InventoryService

router = APIRouter(prefix="/inventory", tags=["inventory"])


def _svc(db: AsyncSession, ctx: TenantContext) -> InventoryService:
    return InventoryService(db, ctx)


# --- Categories ---

@router.post("/categories", response_model=CategoryResponse)
async def create_category(data: CategoryCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).create_category(**data.model_dump())


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_categories()


@router.patch("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: UUID, data: CategoryUpdate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).update_category(category_id, **data.model_dump(exclude_unset=True))


# --- Products ---

@router.post("/products", response_model=ProductResponse)
async def create_product(data: ProductCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).create_product(**data.model_dump())


@router.get("/products", response_model=list[ProductResponse])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    category_id: UUID | None = None,
    is_active: bool | None = None,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db, ctx).get_products(skip=skip, limit=limit, category_id=category_id, is_active=is_active)


@router.get("/products/barcode/{barcode}", response_model=ProductResponse)
async def get_product_by_barcode(barcode: str, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    product = await _svc(db, ctx).get_product_by_barcode(barcode)
    if not product:
        from app.core.exceptions.handlers import NotFoundException
        raise NotFoundException("Product")
    return product


@router.get("/products/sku/{sku}", response_model=ProductResponse)
async def get_product_by_sku(sku: str, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    product = await _svc(db, ctx).get_product_by_sku(sku)
    if not product:
        from app.core.exceptions.handlers import NotFoundException
        raise NotFoundException("Product")
    return product


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_product(product_id)


@router.patch("/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: UUID, data: ProductUpdate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).update_product(product_id, **data.model_dump(exclude_unset=True))


@router.delete("/products/{product_id}")
async def delete_product(product_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    await _svc(db, ctx).delete_product(product_id)
    return {"message": "Product deleted"}


# --- Warehouses ---

@router.post("/warehouses", response_model=WarehouseResponse)
async def create_warehouse(data: WarehouseCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).create_warehouse(**data.model_dump())


@router.get("/warehouses", response_model=list[WarehouseResponse])
async def list_warehouses(ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_warehouses()


@router.get("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(warehouse_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_warehouse(warehouse_id)


@router.patch("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
async def update_warehouse(warehouse_id: UUID, data: WarehouseUpdate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).update_warehouse(warehouse_id, **data.model_dump(exclude_unset=True))


# --- Inventory / Stock ---

@router.get("/stock", response_model=list[InventoryResponse])
async def list_stock(
    product_id: UUID | None = None,
    warehouse_id: UUID | None = None,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db, ctx).get_stock(product_id=product_id, warehouse_id=warehouse_id)


@router.post("/stock/adjust", response_model=InventoryResponse)
async def adjust_stock(data: InventoryAdjustment, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).adjust_stock(
        product_id=data.product_id,
        warehouse_id=data.warehouse_id,
        quantity=data.quantity,
        reason=data.reason,
        notes=data.notes,
    )


# --- Batches ---

@router.post("/batches", response_model=BatchResponse)
async def create_batch(data: BatchCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).create_batch(**data.model_dump())


@router.get("/batches", response_model=list[BatchResponse])
async def list_batches(
    product_id: UUID | None = None,
    warehouse_id: UUID | None = None,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db, ctx).get_batches(product_id=product_id, warehouse_id=warehouse_id)


@router.get("/batches/{batch_id}", response_model=BatchResponse)
async def get_batch(batch_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_batch(batch_id)


# --- Movements ---

@router.post("/movements", response_model=MovementResponse)
async def record_movement(data: MovementCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).record_movement(**data.model_dump())


@router.get("/movements", response_model=list[MovementResponse])
async def list_movements(
    product_id: UUID | None = None,
    warehouse_id: UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db, ctx).get_movements(product_id=product_id, warehouse_id=warehouse_id, skip=skip, limit=limit)


# --- Stock Transfers ---

@router.post("/transfers", response_model=StockTransferResponse)
async def create_transfer(data: StockTransferCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    items = [item.model_dump() for item in data.items]
    return await _svc(db, ctx).create_transfer(
        from_warehouse_id=data.from_warehouse_id,
        to_warehouse_id=data.to_warehouse_id,
        items=items,
        notes=data.notes,
    )


@router.get("/transfers", response_model=list[StockTransferResponse])
async def list_transfers(
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db, ctx).get_transfers(status=status, skip=skip, limit=limit)


@router.get("/transfers/{transfer_id}", response_model=StockTransferResponse)
async def get_transfer(transfer_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_transfer(transfer_id)


@router.patch("/transfers/{transfer_id}/status", response_model=StockTransferResponse)
async def update_transfer_status(transfer_id: UUID, data: TransferStatusUpdate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).update_transfer_status(transfer_id, status=data.status, items_data=data.items)


# --- Stock Alerts ---

@router.get("/alerts", response_model=list[StockAlertResponse])
async def list_alerts(
    is_resolved: bool = False,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db, ctx).get_alerts(is_resolved=is_resolved)


@router.post("/alerts/{alert_id}/resolve", response_model=StockAlertResponse)
async def resolve_alert(alert_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).resolve_alert(alert_id)


@router.post("/alerts/check")
async def check_low_stock(ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    alerts = await _svc(db, ctx).check_low_stock_all()
    return {"new_alerts": len(alerts)}
