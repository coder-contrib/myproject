from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.tenant import TenantContext, get_tenant_context
from app.modules.purchases.schemas import (
    PurchaseOrderCreate, PurchaseOrderResponse, PurchaseOrderStatusUpdate,
    PurchaseInvoiceCreate, PurchaseInvoiceResponse,
    PurchasePaymentCreate,
    PurchaseReturnCreate, PurchaseReturnResponse,
)
from app.modules.purchases.service import PurchaseService

router = APIRouter(prefix="/purchases", tags=["purchases"])


def _svc(db: AsyncSession, ctx: TenantContext) -> PurchaseService:
    return PurchaseService(db, ctx)


# --- Purchase Orders ---

@router.post("/orders", response_model=PurchaseOrderResponse)
async def create_order(data: PurchaseOrderCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    items = [item.model_dump() for item in data.items]
    return await _svc(db, ctx).create_order(
        supplier_id=data.supplier_id,
        warehouse_id=data.warehouse_id,
        order_date=data.order_date,
        expected_date=data.expected_date,
        notes=data.notes,
        items=items,
    )


@router.get("/orders", response_model=list[PurchaseOrderResponse])
async def list_orders(
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db, ctx).get_orders(skip=skip, limit=limit, status=status)


@router.get("/orders/{order_id}", response_model=PurchaseOrderResponse)
async def get_order(order_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_order(order_id)


@router.patch("/orders/{order_id}/status", response_model=PurchaseOrderResponse)
async def update_order_status(order_id: UUID, data: PurchaseOrderStatusUpdate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).update_order_status(order_id, data.status)


# --- Purchase Invoices ---

@router.post("/invoices", response_model=PurchaseInvoiceResponse)
async def create_invoice(data: PurchaseInvoiceCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    items = [item.model_dump() for item in data.items]
    return await _svc(db, ctx).create_invoice(
        supplier_id=data.supplier_id,
        purchase_order_id=data.purchase_order_id,
        issue_date=data.issue_date,
        due_date=data.due_date,
        notes=data.notes,
        items=items,
    )


@router.get("/invoices", response_model=list[PurchaseInvoiceResponse])
async def list_invoices(
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db, ctx).get_invoices(skip=skip, limit=limit, status=status)


@router.get("/invoices/{invoice_id}", response_model=PurchaseInvoiceResponse)
async def get_invoice(invoice_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_invoice(invoice_id)


@router.post("/invoices/{invoice_id}/pay", response_model=PurchaseInvoiceResponse)
async def record_payment(invoice_id: UUID, data: PurchasePaymentCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).record_payment(
        invoice_id=invoice_id,
        amount=data.amount,
        payment_method=data.payment_method,
        payment_date=data.payment_date,
    )


# --- Purchase Returns ---

@router.post("/returns", response_model=PurchaseReturnResponse)
async def create_return(data: PurchaseReturnCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    items = [item.model_dump() for item in data.items]
    return await _svc(db, ctx).create_return(
        invoice_id=data.invoice_id,
        supplier_id=data.supplier_id,
        return_date=data.return_date,
        reason=data.reason,
        items=items,
    )


@router.get("/returns", response_model=list[PurchaseReturnResponse])
async def list_returns(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db, ctx).get_returns(skip=skip, limit=limit)


@router.get("/returns/{return_id}", response_model=PurchaseReturnResponse)
async def get_return(return_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_return(return_id)
