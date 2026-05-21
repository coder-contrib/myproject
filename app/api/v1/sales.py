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
from app.modules.sales.models import SalesInvoice, SalesItem, Quotation, SalesPayment

router = APIRouter(prefix="/sales", tags=["sales"])


class InvoiceCreate(BaseModel):
    customer_id: UUID | None = None
    currency_id: UUID | None = None
    items: list[dict]
    payment_type: str = "cash"
    due_date: str | None = None
    notes: str | None = None


class PaymentCreate(BaseModel):
    invoice_id: UUID
    amount: float
    method: str = "cash"
    treasury_id: UUID | None = None

    @field_validator("amount")
    @classmethod
    def positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v


@router.get("/invoices")
async def list_invoices(
    pagination: PaginationParams = Depends(get_pagination),
    filters: FilterParams = Depends(get_filters),
    sorting: SortParams = Depends(get_sorting),
    search: SearchParams = Depends(get_search),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    base = select(SalesInvoice).where(
        SalesInvoice.tenant_id == ctx.tenant_id,
        SalesInvoice.deleted_at == None,
    )

    base = search.apply_to_query(base, SalesInvoice, searchable_fields=["invoice_number"])
    base = filters.apply_to_query(base, SalesInvoice)
    base = sorting.apply_to_query(base, SalesInvoice)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = base.offset(pagination.skip).limit(pagination.limit)
    result = await db.execute(stmt)
    invoices = result.scalars().all()

    data = [
        {
            "id": str(inv.id),
            "invoice_number": inv.invoice_number,
            "customer_id": str(inv.customer_id) if inv.customer_id else None,
            "subtotal": float(inv.subtotal),
            "discount": float(inv.discount),
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
async def get_invoice(
    invoice_id: UUID,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SalesInvoice).where(
            SalesInvoice.id == invoice_id,
            SalesInvoice.tenant_id == ctx.tenant_id,
        )
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    items_result = await db.execute(
        select(SalesItem).where(SalesItem.invoice_id == invoice_id)
    )
    items = items_result.scalars().all()

    return success_response(data={
        "id": str(invoice.id),
        "invoice_number": invoice.invoice_number,
        "customer_id": str(invoice.customer_id) if invoice.customer_id else None,
        "subtotal": float(invoice.subtotal),
        "discount": float(invoice.discount),
        "total": float(invoice.total),
        "amount_paid": float(invoice.amount_paid),
        "balance_due": float(invoice.total - invoice.amount_paid),
        "status": invoice.status,
        "payment_type": invoice.payment_type,
        "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
        "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
        "items": [
            {
                "id": str(item.id),
                "product_id": str(item.product_id),
                "quantity": float(item.quantity),
                "unit_price": float(item.unit_price),
                "discount": float(item.discount),
                "tax_amount": float(item.tax_amount),
                "total": float(item.total),
            }
            for item in items
        ],
    })


@router.post("/invoices")
async def create_invoice(
    data: InvoiceCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    from app.modules.sales.service import SalesService

    svc = SalesService(db, ctx)
    invoice = await svc.create_invoice(
        customer_id=data.customer_id,
        items=data.items,
        payment_type=data.payment_type,
    )

    return success_response(
        data={"id": str(invoice.id), "invoice_number": invoice.invoice_number, "total": float(invoice.total)},
        message="Invoice created",
    )


@router.post("/payments")
async def record_payment(
    data: PaymentCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    from app.modules.sales.service import SalesService

    svc = SalesService(db, ctx)
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


@router.get("/quotations")
async def list_quotations(
    pagination: PaginationParams = Depends(get_pagination),
    filters: FilterParams = Depends(get_filters),
    sorting: SortParams = Depends(get_sorting),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    base = select(Quotation).where(Quotation.tenant_id == ctx.tenant_id)
    base = filters.apply_to_query(base, Quotation)
    base = sorting.apply_to_query(base, Quotation)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = base.offset(pagination.skip).limit(pagination.limit)
    result = await db.execute(stmt)
    quotations = result.scalars().all()

    data = [
        {
            "id": str(q.id),
            "quotation_number": q.quotation_number,
            "customer_id": str(q.customer_id) if q.customer_id else None,
            "total": float(q.total),
            "status": q.status,
            "valid_until": q.valid_until.isoformat() if q.valid_until else None,
            "created_at": q.created_at.isoformat() if q.created_at else None,
        }
        for q in quotations
    ]

    return paginated_response(data=data, total=total, page=pagination.page, per_page=pagination.per_page)
