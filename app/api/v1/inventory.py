from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.tenant import TenantContext, get_tenant_context
from app.core.api import (
    PaginationParams, get_pagination,
    FilterParams, get_filters,
    SortParams, get_sorting,
    SearchParams, get_search,
)
from app.core.api.response import paginated_response, success_response
from app.modules.inventory.models import (
    Inventory, InventoryMovement, StockTransfer, Warehouse,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


class StockAdjustment(BaseModel):
    product_id: UUID
    warehouse_id: UUID
    quantity: int
    reason: str = "adjustment"

    @field_validator("quantity")
    @classmethod
    def non_zero(cls, v: int) -> int:
        if v == 0:
            raise ValueError("Quantity cannot be zero")
        return v


class TransferCreate(BaseModel):
    from_warehouse_id: UUID
    to_warehouse_id: UUID
    items: list[dict]
    notes: str | None = None


@router.get("/stock")
async def list_stock(
    pagination: PaginationParams = Depends(get_pagination),
    filters: FilterParams = Depends(get_filters),
    sorting: SortParams = Depends(get_sorting),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    base = (
        select(Inventory)
        .join(Warehouse, Inventory.warehouse_id == Warehouse.id)
        .where(Warehouse.tenant_id == ctx.tenant_id)
    )

    base = filters.apply_to_query(base, Inventory)
    base = sorting.apply_to_query(base, Inventory)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = base.offset(pagination.skip).limit(pagination.limit)
    result = await db.execute(stmt)
    items = result.scalars().all()

    data = [
        {
            "id": str(inv.id),
            "product_id": str(inv.product_id),
            "warehouse_id": str(inv.warehouse_id),
            "quantity": inv.quantity,
            "reserved_quantity": inv.reserved_quantity,
            "available_quantity": inv.quantity - inv.reserved_quantity - inv.damaged_quantity,
        }
        for inv in items
    ]

    return paginated_response(data=data, total=total, page=pagination.page, per_page=pagination.per_page)


@router.post("/adjust")
async def adjust_stock(
    data: StockAdjustment,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Inventory).where(
            Inventory.product_id == data.product_id,
            Inventory.warehouse_id == data.warehouse_id,
        )
    )
    inv = result.scalar_one_or_none()

    if inv:
        inv.quantity += data.quantity
        if inv.quantity < 0:
            raise HTTPException(status_code=400, detail="Insufficient stock")
    else:
        if data.quantity < 0:
            raise HTTPException(status_code=400, detail="Cannot have negative stock")
        inv = Inventory(
            product_id=data.product_id,
            warehouse_id=data.warehouse_id,
            quantity=data.quantity,
        )
        db.add(inv)

    movement = InventoryMovement(
        tenant_id=ctx.tenant_id,
        product_id=data.product_id,
        to_warehouse_id=data.warehouse_id if data.quantity > 0 else None,
        from_warehouse_id=data.warehouse_id if data.quantity < 0 else None,
        quantity=abs(data.quantity),
        reason=data.reason,
        created_by=ctx.user_id,
    )
    db.add(movement)
    await db.flush()

    return success_response(
        data={"product_id": str(data.product_id), "new_quantity": inv.quantity},
        message="Stock adjusted",
    )


@router.get("/movements")
async def list_movements(
    pagination: PaginationParams = Depends(get_pagination),
    filters: FilterParams = Depends(get_filters),
    sorting: SortParams = Depends(get_sorting),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    base = select(InventoryMovement).where(InventoryMovement.tenant_id == ctx.tenant_id)
    base = filters.apply_to_query(base, InventoryMovement)
    base = sorting.apply_to_query(base, InventoryMovement)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = base.offset(pagination.skip).limit(pagination.limit)
    result = await db.execute(stmt)
    movements = result.scalars().all()

    data = [
        {
            "id": str(m.id),
            "product_id": str(m.product_id),
            "from_warehouse_id": str(m.from_warehouse_id) if m.from_warehouse_id else None,
            "to_warehouse_id": str(m.to_warehouse_id) if m.to_warehouse_id else None,
            "quantity": m.quantity,
            "reason": m.reason,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in movements
    ]

    return paginated_response(data=data, total=total, page=pagination.page, per_page=pagination.per_page)


@router.get("/warehouses")
async def list_warehouses(
    pagination: PaginationParams = Depends(get_pagination),
    search: SearchParams = Depends(get_search),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    base = select(Warehouse).where(Warehouse.tenant_id == ctx.tenant_id, Warehouse.deleted_at == None)
    base = search.apply_to_query(base, Warehouse, searchable_fields=["name", "location"])

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = base.offset(pagination.skip).limit(pagination.limit)
    result = await db.execute(stmt)
    warehouses = result.scalars().all()

    data = [
        {
            "id": str(w.id),
            "name": w.name,
            "location": w.location,
            "branch_id": str(w.branch_id) if w.branch_id else None,
            "created_at": w.created_at.isoformat() if w.created_at else None,
        }
        for w in warehouses
    ]

    return paginated_response(data=data, total=total, page=pagination.page, per_page=pagination.per_page)


@router.get("/transfers")
async def list_transfers(
    pagination: PaginationParams = Depends(get_pagination),
    filters: FilterParams = Depends(get_filters),
    sorting: SortParams = Depends(get_sorting),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    base = select(StockTransfer).where(StockTransfer.tenant_id == ctx.tenant_id)
    base = filters.apply_to_query(base, StockTransfer)
    base = sorting.apply_to_query(base, StockTransfer)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = base.offset(pagination.skip).limit(pagination.limit)
    result = await db.execute(stmt)
    transfers = result.scalars().all()

    data = [
        {
            "id": str(t.id),
            "transfer_number": t.transfer_number,
            "from_warehouse_id": str(t.from_warehouse_id),
            "to_warehouse_id": str(t.to_warehouse_id),
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in transfers
    ]

    return paginated_response(data=data, total=total, page=pagination.page, per_page=pagination.per_page)
