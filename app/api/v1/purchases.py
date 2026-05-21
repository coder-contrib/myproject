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
from app.modules.purchases.models import PurchaseOrder, PurchaseInvoice, PurchaseInvoiceItem

router = APIRouter(prefix="/purchases", tags=["purchases"])


class PurchaseOrderCreate(BaseModel):
    supplier_id: UUID
    items: list[dict]
    notes: str | None = None


class PurchaseInvoiceCreate(BaseModel):
    supplier_id: UUID
    purchase_order_id: UUID | None = None
    items: list[dict]
    due_date: str | None = None


class PurchasePaymentCreate(BaseModel):
    invoice_id: UUID
    amount: float
    method: str = "bank_transfer"
    treasury_id: UUID | None = None

    @field_validator("amount")
    @classmethod
    def positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v


@router.get("/orders")
async def list_purchase_orders(
    pagination: PaginationParams = Depends(get_pagination),
    filters: FilterParams = Depends(get_filters),
    sorting: SortParams = Depends(get_sorting),
    search: SearchParams = Depends(get_search),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    base = select(PurchaseOrder).where(PurchaseOrder.tenant_id == ctx.tenant_id)
    base = search.apply_to_query(base, PurchaseOrder, searchable_fields=["order_number"])
    base = filters.apply_to_query(base, PurchaseOrder)
    base = sorting.apply_to_query(base, PurchaseOrder)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = base.offset(pagination.skip).limit(pagination.limit)
    result = await db.execute(stmt)
    orders = result.scalars().all()

    data = [
        {
            "id": str(o.id),
            "order_number": o.order_number,
            "supplier_id": str(o.supplier_id) if o.supplier_id else None,
            "total": float(o.total),
            "status": o.status,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in orders
    ]

    return paginated_response(data=data, total=total, page=pagination.page, per_page=pagination.per_page)


@router.post("/orders")
async def create_purchase_order(
    data: PurchaseOrderCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    from app.modules.purchases.service import PurchaseService

    svc = PurchaseService(db, ctx)
    order = await svc.create_order(
        supplier_id=data.supplier_id,
        items=data.items,
    )

    return success_response(
        data={"id": str(order.id), "order_number": order.order_number, "total": float(order.total)},
        message="Purchase order created",
    )


@router.get("/orders/{order_id}")
async def get_purchase_order(
    order_id: UUID,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.id == order_id,
            PurchaseOrder.tenant_id == ctx.tenant_id,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    return success_response(data={
        "id": str(order.id),
        "order_number": order.order_number,
        "supplier_id": str(order.supplier_id) if order.supplier_id else None,
        "total": float(order.total),
        "status": order.status,
        "items": [
            {
                "id": str(item.id),
                "product_id": str(item.product_id),
                "quantity": float(item.quantity),
                "unit_price": float(item.unit_price),
                "total": float(item.total),
            }
            for item in order.items
        ],
        "created_at": order.created_at.isoformat() if order.created_at else None,
    })


@router.get("/invoices")
async def list_purchase_invoices(
    pagination: PaginationParams = Depends(get_pagination),
    filters: FilterParams = Depends(get_filters),
    sorting: SortParams = Depends(get_sorting),
    search: SearchParams = Depends(get_search),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    base = select(PurchaseInvoice).where(
        PurchaseInvoice.tenant_id == ctx.tenant_id,
        PurchaseInvoice.deleted_at == None,
    )
    base = search.apply_to_query(base, PurchaseInvoice, searchable_fields=["invoice_number"])
    base = filters.apply_to_query(base, PurchaseInvoice)
    base = sorting.apply_to_query(base, PurchaseInvoice)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = base.offset(pagination.skip).limit(pagination.limit)
    result = await db.execute(stmt)
    invoices = result.scalars().all()

    data = [
        {
            "id": str(inv.id),
            "invoice_number": inv.invoice_number,
            "supplier_id": str(inv.supplier_id) if inv.supplier_id else None,
            "total": float(inv.total),
            "amount_paid": float(inv.amount_paid),
            "status": inv.status,
            "due_date": inv.due_date.isoformat() if inv.due_date else None,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
        }
        for inv in invoices
    ]

    return paginated_response(data=data, total=total, page=pagination.page, per_page=pagination.per_page)


@router.get("/invoices/{invoice_id}")
async def get_purchase_invoice(
    invoice_id: UUID,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PurchaseInvoice).where(
            PurchaseInvoice.id == invoice_id,
            PurchaseInvoice.tenant_id == ctx.tenant_id,
        )
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Purchase invoice not found")

    return success_response(data={
        "id": str(invoice.id),
        "invoice_number": invoice.invoice_number,
        "supplier_id": str(invoice.supplier_id) if invoice.supplier_id else None,
        "total": float(invoice.total),
        "amount_paid": float(invoice.amount_paid),
        "balance_due": float(invoice.total - invoice.amount_paid),
        "status": invoice.status,
        "items": [
            {
                "id": str(item.id),
                "product_id": str(item.product_id),
                "quantity": float(item.quantity),
                "unit_price": float(item.unit_price),
            }
            for item in invoice.items
        ],
        "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
    })


@router.post("/invoices")
async def create_purchase_invoice(
    data: PurchaseInvoiceCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    from app.modules.purchases.service import PurchaseService

    svc = PurchaseService(db, ctx)
    invoice = await svc.create_invoice(
        supplier_id=data.supplier_id,
        items=data.items,
        purchase_order_id=data.purchase_order_id,
    )

    return success_response(
        data={"id": str(invoice.id), "invoice_number": invoice.invoice_number, "total": float(invoice.total)},
        message="Purchase invoice created",
    )


@router.post("/payments")
async def record_purchase_payment(
    data: PurchasePaymentCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    from app.modules.purchases.service import PurchaseService

    svc = PurchaseService(db, ctx)
    payment = await svc.record_payment(
        invoice_id=data.invoice_id,
        amount=data.amount,
        method=data.method,
        treasury_id=data.treasury_id,
    )

    return success_response(
        data={"id": str(payment.id), "amount": float(payment.amount)},
        message="Payment recorded",
    )
